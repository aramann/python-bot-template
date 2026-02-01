"""
Unit of Work — единая точка доступа ко всем репозиториям.

Использование:
    async with get_session() as session:
        uow = UnitOfWork(session)
        user = await uow.users.get_by_id(1)
        await uow.orders.create(...)

    # или в FastAPI:
    @router.get("/")
    async def handler(uow: UnitOfWork = Depends(get_uow)):
        user = await uow.users.get_by_id(1)
"""

from sqlalchemy.ext.asyncio import AsyncSession

from common.db.postgres.interactors.user import UserRepository


class UnitOfWork:
    """
    Unit of Work — контейнер для всех репозиториев.

    Все репозитории используют одну сессию = одну транзакцию.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)
        # Добавляй новые репозитории сюда:
        # self.orders = OrderRepository(session)
        # self.payments = PaymentRepository(session)
        # self.logs = LogRepository(session)
