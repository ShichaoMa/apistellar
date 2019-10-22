# Create a database instance, and connect to it.


class SqlAlchemyType(PersistentType, metaclass=SqlAlchemyTypeMeta):
    pass


class HighScores(SqlAlchemyType, SqliteDriverMixin):

    TABLE = "HighScores"

    id = validators.Integer()
    name = validators.String(max_length=100)
    score = validators.Integer()

    async def insert(self):
        values = [
            {"name": "Daisy", "score": 92},
            {"name": "Neil", "score": 87},
            {"name": "Carol", "score": 43},
        ]
        await self.conn.execute_many(self.model.insert(), values)

    @classmethod
    async def list(cls):
        rows = await cls.conn.fetch_all(sqlalchemy.select([cls.model]))
        print('High Scores:', rows)


if __name__ == "__main__":
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(HighScores().insert())
    loop.run_until_complete(HighScores().list())
