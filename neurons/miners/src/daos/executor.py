from typing import Optional
from daos.base import BaseDao
from models.executor import Executor


class ExecutorDao(BaseDao):
    def save(self, executor: Executor) -> Executor:
        self.session.add(executor)
        self.session.commit()
        self.session.refresh(executor)
        return executor

    def get_executor_by_address_port_validator(self, address: str, port: int, validator: str) -> Optional[Executor]:
        """Get executor by address, port and validator combination"""
        return self.session.query(Executor).filter_by(
            address=address, 
            port=port,
            validator=validator
        ).first()
        
    def delete_by_address_port(self, address: str, port: int) -> None:
        executor = self.session.query(Executor).filter_by(
            address=address, port=port).first()
        if executor:
            self.session.delete(executor)
            self.session.commit()
    
    def delete_by_address_port_validator(self, address: str, port: int, validator: str) -> None:
        executor = self.session.query(Executor).filter_by(
            address=address, port=port, validator=validator).first()
        if executor:
            self.session.delete(executor)
            self.session.commit()
            

    def get_executors_for_validator(self, validator_key: str, executor_id: Optional[str] = None) -> list[Executor]:
        """Get executors that opened to valdiator

        Args:
            validator_key (str): validator hotkey string

        Return:
            List[Executor]: list of Executors
        """
        if executor_id:
            return list(self.session.query(Executor).filter_by(validator=validator_key, uuid=executor_id))

        return list(self.session.query(Executor).filter_by(validator=validator_key))

    def get_all_executors(self) -> list[Executor]:
        return list(self.session.query(Executor).all())
