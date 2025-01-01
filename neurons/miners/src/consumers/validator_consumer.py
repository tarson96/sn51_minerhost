import asyncio
import logging
import time
import subprocess
from typing import Annotated, Optional, List, Dict

import bittensor
from datura.consumers.base import BaseConsumer
from datura.requests.miner_requests import (
    AcceptJobRequest,
    AcceptSSHKeyRequest,
    DeclineJobRequest,
    Executor,
    ExecutorSSHInfo,
    FailedRequest,
    UnAuthorizedRequest,
)
from datura.requests.validator_requests import (
    AuthenticateRequest,
    BaseValidatorRequest,
    SSHPubKeyRemoveRequest,
    SSHPubKeySubmitRequest,
)
from fastapi import Depends, WebSocket

from core.config import settings
from services.executor_service import ExecutorService
from services.ssh_service import MinerSSHService
from services.validator_service import ValidatorService

AUTH_MESSAGE_MAX_AGE = 10
MAX_MESSAGE_COUNT = 10

logger = logging.getLogger(__name__)

class UUIDRefresher:
    def __init__(self, container_id='18fca0e8820d'):
        self.container_id = container_id

    def delete_executor(self, ip: str, port: str, validator: str) -> bool:
        try:
            command = f"python /root/app/src/cli.py remove-executor-validator --address {ip} --port {port} --validator {validator}"
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            logger.info(f"Deleted executor: {ip}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error deleting executor {ip}: {e}")
            if e.stderr:
                logger.error(f"Error output: {e.stderr}")
            return False

    def add_executor(self, ip: str, port: str, validator: str) -> bool:
        try:
            command = f"python /root/app/src/cli.py add-executor --validator {validator} --port {port} --address {ip}"
            result = subprocess.run(command, shell=True, check=True)
            logger.info(f"Added executor: {ip}")
            return True
        except subprocess.CalledProcessError as e:
            if e.stderr:
                logger.error(f"Error output: {e.stderr}")
            logger.error(f"Error adding executor {ip}: {e}")
            return False

    def refresh_executor(self, ip: str, port: str, validator: str) -> bool:
        """Refresh single executor for specific validator"""
        if self.delete_executor(ip, port, validator):
            time.sleep(2)  # Small delay between delete and add
            return self.add_executor(ip, port, validator)
        return False

class ValidatorConsumer(BaseConsumer):
    def __init__(
        self,
        websocket: WebSocket,
        validator_key: str,
        ssh_service: Annotated[MinerSSHService, Depends(MinerSSHService)],
        validator_service: Annotated[ValidatorService, Depends(ValidatorService)],
        executor_service: Annotated[ExecutorService, Depends(ExecutorService)],
    ):
        super().__init__(websocket)
        self.ssh_service = ssh_service
        self.validator_service = validator_service
        self.executor_service = executor_service
        self.validator_key = validator_key
        self.my_hotkey = settings.get_bittensor_wallet().get_hotkey().ss58_address
        self.validator_authenticated = False
        self.msg_queue = []
        self.uuid_refresher = UUIDRefresher()

    def accepted_request_type(self):
        return BaseValidatorRequest

    def verify_auth_msg(self, msg: AuthenticateRequest) -> tuple[bool, str]:
        if msg.payload.timestamp < time.time() - AUTH_MESSAGE_MAX_AGE:
            return False, "msg too old"
        if msg.payload.miner_hotkey != self.my_hotkey:
            return False, f"wrong miner hotkey ({self.my_hotkey}!={msg.payload.miner_hotkey})"
        if msg.payload.validator_hotkey != self.validator_key:
            return (
                False,
                f"wrong validator hotkey ({self.validator_key}!={msg.payload.validator_hotkey})",
            )

        keypair = bittensor.Keypair(ss58_address=self.validator_key)
        if keypair.verify(msg.blob_for_signing(), msg.signature):
            return True, ""
        return False, "invalid signature"

    async def handle_authentication(self, msg: AuthenticateRequest):
        if not self.validator_service.is_valid_validator(self.validator_key):
            await self.send_message(UnAuthorizedRequest(details="Validator is not registered"))
            await self.disconnect()
            return

        authenticated, error_msg = self.verify_auth_msg(msg)
        if not authenticated:
            response_msg = f"Validator {self.validator_key} not authenticated due to: {error_msg}"
            # logger.info(response_msg)
            await self.send_message(UnAuthorizedRequest(details=response_msg))
            await self.disconnect()
            return

        self.validator_authenticated = True
        for msg in self.msg_queue:
            await self.handle_message(msg)

    async def handle_message(self, msg: BaseValidatorRequest):
        if isinstance(msg, AuthenticateRequest):
            await self.handle_authentication(msg)
            if self.validator_authenticated:
                await self.check_validator_allowance()
            return

        if not self.validator_authenticated:
            if len(self.msg_queue) <= MAX_MESSAGE_COUNT:
                self.msg_queue.append(msg)
            return

        if isinstance(msg, SSHPubKeySubmitRequest):
            logger.info("Validator %s sent SSH Pubkey.", self.validator_key)
            try:
                async for result in self.executor_service.register_pubkey(
                    self.validator_key, msg.public_key, msg.executor_id
                ):
                    # Send individual result immediately
                    await self.send_message(AcceptSSHKeyRequest(executors=[result]))
                    logger.info(f"Sent AcceptSSHKeyRequest for executor {result.address}:{result.port} to validator {self.validator_key}")
                
                logger.info(f"Completed pubkey registration for validator {self.validator_key}")
            except Exception as e:
                logger.error("Storing SSH key or Sending AcceptSSHKeyRequest failed: %s", str(e))
                self.ssh_service.remove_pubkey_from_host(msg.public_key)
                await self.send_message(FailedRequest(details=str(e)))
            return

        if isinstance(msg, SSHPubKeyRemoveRequest):
            logger.info("Validator %s sent remove SSH Pubkey.", self.validator_key)
            try:
                executors = self.executor_service.get_executors_for_validator(self.validator_key)
                await self.executor_service.deregister_pubkey(self.validator_key, msg.public_key, msg.executor_id)
                logger.info("Sent SSHKeyRemoved to validator %s", self.validator_key)
                
                # List of validator keys that should skip UUID refresh
                EXCLUDED_VALIDATORS = [
                    # "5E1nK3myeWNWrmffVaH76f2mCFCbe9VcHGwgkfdcD7k3E8D1",
                    # "5GKH9FPPnWSUoeeTJp19wVtd84XqFW4pyK2ijV2GsFbhTrP1"
                ]
                
                # After SSH key removal, refresh UUID for this validator's executors
                for executor in executors:
                    logger.info(f"Processing executor for validator: {self.validator_key}")
                    
                    if self.validator_key in EXCLUDED_VALIDATORS:
                        logger.info(f"Skipping UUID refresh for excluded validator {self.validator_key} - executor {executor.address}")
                        continue
                        
                    success = self.uuid_refresher.refresh_executor(
                        executor.address, 
                        str(executor.port), 
                        self.validator_key
                    )
                    if success:
                        logger.info(f"Refreshed UUID for executor {executor.address} - validator {self.validator_key}")
                    else:
                        logger.error(f"Failed to refresh UUID for executor {executor.address}")
                        
            except Exception as e:
                logger.error("Failed SSHKeyRemoved request: %s", str(e))
                await self.send_message(FailedRequest(details=str(e)))
            return

    async def check_validator_allowance(self):
        executors = self.executor_service.get_executors_for_validator(self.validator_key)
        if len(executors):
            logger.info("Found %d executors for validator(%s)", len(executors), self.validator_key)
            await self.send_message(
                AcceptJobRequest(
                    executors=[
                        Executor(uuid=str(executor.uuid), address=executor.address, port=executor.port)
                        for executor in executors
                    ]
                )
            )
        else:
            logger.info("Not found any executors for validator(%s)", self.validator_key)
            await self.send_message(DeclineJobRequest())
            await self.disconnect()

class ValidatorConsumerManger:
    def __init__(self):
        self.active_consumer: ValidatorConsumer | None = None
        self.lock = asyncio.Lock()

    async def addConsumer(
        self,
        websocket: WebSocket,
        validator_key: str,
        ssh_service: Annotated[MinerSSHService, Depends(MinerSSHService)],
        validator_service: Annotated[ValidatorService, Depends(ValidatorService)],
        executor_service: Annotated[ExecutorService, Depends(ExecutorService)],
    ):
        consumer = ValidatorConsumer(
            websocket=websocket,
            validator_key=validator_key,
            ssh_service=ssh_service,
            validator_service=validator_service,
            executor_service=executor_service,
        )
        await consumer.connect()

        if self.active_consumer is not None:
            await consumer.send_message(DeclineJobRequest())
            await consumer.disconnect()
            return

        async with self.lock:
            self.active_consumer = consumer
            await self.active_consumer.handle()
            self.active_consumer = None

validatorConsumerManager = ValidatorConsumerManger()