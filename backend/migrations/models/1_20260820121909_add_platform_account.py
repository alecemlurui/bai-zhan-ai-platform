from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "platform_accounts" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "platform" VARCHAR(64) NOT NULL,
    "account_name" VARCHAR(256) NOT NULL,
    "credentials" JSON NOT NULL,
    "is_active" INT NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL,
    "owner_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
        ALTER TABLE "publish_records" ADD "account_id" INT;
        ALTER TABLE "publish_records" ADD CONSTRAINT "fk_publish__platform_0d575102" FOREIGN KEY ("account_id") REFERENCES "platform_accounts" ("id") ON DELETE CASCADE;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "publish_records" DROP FOREIGN KEY "fk_publish__platform_0d575102";
        ALTER TABLE "publish_records" DROP COLUMN "account_id";
        DROP TABLE IF EXISTS "platform_accounts";"""


MODELS_STATE = (
    "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"
)
