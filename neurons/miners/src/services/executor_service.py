import asyncio
import json
import logging
from typing import Annotated, Optional

import aiohttp
import bittensor
from datura.requests.miner_requests import ExecutorSSHInfo
from fastapi import Depends

from core.config import settings
from daos.executor import ExecutorDao
from models.executor import Executor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExecutorService:
    def __init__(self, executor_dao: Annotated[ExecutorDao, Depends(ExecutorDao)]):
        self.executor_dao = executor_dao

    def get_executors_for_validator(self, validator_hotkey: str, executor_id: Optional[str] = None):
        return self.executor_dao.get_executors_for_validator(validator_hotkey, executor_id)

    async def send_pubkey_to_executor(
        self, executor: Executor, pubkey: str
    ) -> ExecutorSSHInfo | None:
        """TODO: Send API request to executor with pubkey

        Args:
            executor (Executor): Executor instance that register validator hotkey
            pubkey (str): SSH public key from validator

        Return:
            response (ExecutorSSHInfo | None): Executor SSH connection info.
        """
        timeout = aiohttp.ClientTimeout(total=100)  # 5 seconds timeout
        url = f"http://{executor.address}:{executor.port}/upload_ssh_key"
        keypair: bittensor.Keypair = settings.get_bittensor_wallet().get_hotkey()
        payload = {"public_key": pubkey, "signature": f"0x{keypair.sign(pubkey).hex()}"}
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        logger.error("API request failed to register SSH key. url=%s", url)
                        return None
                    response_obj: dict = await response.json()
                    logger.info(
                        "Get response from Executor(%s:%s): %s",
                        executor.address,
                        executor.port,
                        json.dumps(response_obj),
                    )
                    response_obj["uuid"] = str(executor.uuid)
                    response_obj["address"] = executor.address
                    response_obj["port"] = executor.port
                    return ExecutorSSHInfo.parse_obj(response_obj)
            except Exception as e:
                logger.error(
                    "API request failed to register SSH key. url=%s, error=%s", url, str(e)
                )

    async def remove_pubkey_from_executor(self, executor: Executor, pubkey: str):
        """TODO: Send API request to executor to cleanup pubkey

        Args:
            executor (Executor): Executor instance that needs to remove pubkey
        """
        timeout = aiohttp.ClientTimeout(total=100)  # 5 seconds timeout
        url = f"http://{executor.address}:{executor.port}/remove_ssh_key"
        keypair: bittensor.Keypair = settings.get_bittensor_wallet().get_hotkey()
        payload = {"public_key": pubkey, "signature": f"0x{keypair.sign(pubkey).hex()}"}
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        logger.error("API request failed to register SSH key. url=%s", url)
                        return None
            except Exception as e:
                logger.error(
                    "API request failed to register SSH key. url=%s, error=%s", url, str(e)
                )

    async def register_pubkey(self, validator_hotkey: str, pubkey: bytes, executor_id: Optional[str] = None):
        executors = self.get_executors_for_validator(validator_hotkey, executor_id)
        
        async def process_executor(executor):
            try:
                result = await self.send_pubkey_to_executor(executor, pubkey.decode("utf-8"))
                if result:
                    logger.info(f"Registered pubkey for executor {executor.address}:{executor.port}")
                    return result
            except Exception as e:
                logger.error(f"Failed to register pubkey for executor {executor.address}:{executor.port}: {str(e)}")
            return None

        tasks = [asyncio.create_task(process_executor(executor)) for executor in executors]
        
        results = []
        for completed_task in asyncio.as_completed(tasks):
            result = await completed_task
            if result:
                results.append(result)
                yield result  # This allows us to send results as they become available

        logger.info(f"Registered pubkey with {len(results)} out of {len(executors)} executors for validator {validator_hotkey}")

    async def deregister_pubkey(self, validator_hotkey: str, pubkey: bytes, executor_id: Optional[str] = None):
        """Deregister pubkey from executors.

        Args:
            validator_hotkey (str): Validator hotkey
            pubkey (bytes): validator pubkey
        """
        tasks = [
            asyncio.create_task(
                self.remove_pubkey_from_executor(executor, pubkey.decode("utf-8")),
                name=f"{executor}.remove_pubkey_from_executor",
            )
            for executor in self.get_executors_for_validator(validator_hotkey, executor_id)
        ]
        await asyncio.gather(*tasks, return_exceptions=True)