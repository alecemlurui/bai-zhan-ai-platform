from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "tasks" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "type" VARCHAR(64) NOT NULL,
    "payload" JSON NOT NULL,
    "status" VARCHAR(7) NOT NULL /* PENDING: pending\nRUNNING: running\nSUCCESS: success\nFAILED: failed */,
    "attempts" INT NOT NULL,
    "max_attempts" INT NOT NULL,
    "result" JSON,
    "logs" JSON NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL
);
CREATE TABLE IF NOT EXISTS "users" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "username" VARCHAR(128) NOT NULL UNIQUE,
    "email" VARCHAR(256),
    "password_hash" VARCHAR(256) NOT NULL,
    "role" VARCHAR(5) NOT NULL /* USER: user\nADMIN: admin */,
    "is_active" INT NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL
);
CREATE TABLE IF NOT EXISTS "bots" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(128) NOT NULL,
    "config" JSON NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "owner_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "materials" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "type" VARCHAR(5) NOT NULL /* TEXT: text\nIMAGE: image */,
    "content" TEXT,
    "url" VARCHAR(2048),
    "tags" JSON NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL,
    "owner_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "media" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "url" VARCHAR(2048) NOT NULL,
    "type" VARCHAR(5) NOT NULL /* IMAGE: image\nVIDEO: video */,
    "width" INT,
    "height" INT,
    "size_bytes" INT,
    "created_at" TIMESTAMP NOT NULL,
    "owner_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "topics" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "title" VARCHAR(256) NOT NULL,
    "params" JSON NOT NULL,
    "status" VARCHAR(17) NOT NULL /* CREATED: created\nGENERATING_TITLES: generating_titles\nCOMPLETED: completed */,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "titles" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "text" TEXT NOT NULL,
    "score" REAL,
    "is_selected" INT NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "topic_id" INT NOT NULL REFERENCES "topics" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "articles" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "content" TEXT NOT NULL,
    "status" VARCHAR(10) NOT NULL /* DRAFT: draft\nGENERATING: generating\nCOMPLETED: completed\nPUBLISHED: published */,
    "metadata" JSON NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL,
    "title_id" INT NOT NULL REFERENCES "titles" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "publish_records" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "platform" VARCHAR(64) NOT NULL,
    "status" VARCHAR(10) NOT NULL /* PENDING: pending\nPROCESSING: processing\nSUCCESS: success\nFAILED: failed */,
    "ext_id" VARCHAR(256),
    "error_message" TEXT,
    "result" JSON NOT NULL,
    "created_at" TIMESTAMP NOT NULL,
    "updated_at" TIMESTAMP NOT NULL,
    "article_id" INT NOT NULL REFERENCES "articles" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSON NOT NULL
);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "eJztXW1zmzgQ/isMn9qZXCdJk7TjubkZv5DWV8fO2KTX6eWGkUG2mYJwQTTJ9frfTxJg3j"
    "G4NjFUnxKvtCCelcQ+u0L6LpqWBg3nVdfGumpAsSN8FxEw6T/JohNBBOt1WEAFGMyZkgi8"
    "SkwI5g62gYqJfAEMBxKRBh3V1tdYtxCRItcwqNBSSUUdLUORi/SvLlSwtYR4BW1S8Pc/RK"
    "wjDT6Si/s/11+UhQ4NLdZaXaP3ZnIFP62ZbIjwNatI7zZXVMtwTRRWXj/hlYU2tXWEqXQJ"
    "EbQBhvTy2HZp82nr/CcNnshraVjFa2JER4ML4Bo48rhzJZSJijKeyMpMkhVFrACQaiEKLm"
    "mqw55+SZvw2/nZxZuLt6+vLt6SKqyZG8mbH96tQ2A8RQbPWBZ/sHKAgVeDYRyCSm6HoQdL"
    "HFkZPuZAG1FJ4EsansQ3QLMI4EAQIhz2qhogLsBPlj7J9Mqm43w1qGD8sTvtv+9OX9x0P7"
    "1kJU9+yWgyfhdUt8jg8EbNuD+a9JgJQsgdDLDrpBHvr4AtIddkqA9JEwFSYQr9ULs+8EXN"
    "BgssVsNfHEy713JHYLr36J00lqZdeTh+1xH8NhKj3KP+5OZ2JMnSoCOolrk2IGn6Pbq964"
    "2Gs/dUunbnhu6soNcRtw8YEzwqBkRLvCI/z04LrBvY8uz0ZcJqfsk5K4pbz4QY0NGUtt+f"
    "s8k4e8REdRJW03QVC/8J5AlTU9PerPf7wkUqtYowd3WDwO68orf9o6JB9zGgKEbFAyo5di"
    "hkloOXNrsKu0ByQKk2pJApIGMaG5ASrJswZyqLaSZN46u+Cv5p4NwmkgfUJsh48l9bRXPd"
    "8Eaayd2b25h9Bl1ZoiXnsckukL64SthscxHhr6H8XqA/hc+TsZQ046ae/FmkbQIuthRkPS"
    "hAi7xhA2mAWszq7lrb0epxTW71Y7F6gFHE7H7rQ6tjHRtQqeQKRlW2O4RNMO8efELqZS++"
    "ZLqEDK80vteWDfUl+gCfUg5KAlWfVsjBdRoG74+gAwXScEKywcOGmMT6FXl68szEd2GOXH"
    "fW7w4kkYE8B+qXB2BrSg7avnuj2FC1bC3DLez5F7j+MIUGYA+TC/mtd7Epu1aLoGdIWudW"
    "BMEYtuki89xMSgACS/ZI9N70Tj5oPQuLGayYik+KGPHcwpwNt4sNs78pWCkxy8Y1qN8KHp"
    "xgTudvy1Cn87f53ImWJTx1Cy30ZRXqFGpw4sSJE3eh90CcrAdiiWoudFSFu9DbXWiG1x5c"
    "6DsHNvFNUtaDjnarqh70IT3CGwK1rQMjyy3clBX6hqZfizuI7XIQGTSZDuL2yH2gW2PcHs"
    "PHymF7msQgRiOa92h4030ndQTdJONkl/D7ZQkX8jLXgbzMcB/rTlb5nffIZtbaclWubVTh"
    "Q371NiAd78jnpxdl6BCtltudvcI4vhgsM0I++XQoqH8cZIjej5MhToYaTIZ4FqltVi+TRe"
    "IUmFPgWhy15lJgqOlAzOK/rOCkkPxuqnDi26TRfFJAfGskAsc2lGtiAs2KLIQhgQqhhWg4"
    "4R59HA6kSUf4pmvQOoLgwoOukcuWnzk29XfyBo6N7e5l+gjBXJGX/CrDpc5FM1TgcKbhdP"
    "R/oTJ/wjAjWJALaVyJw5qGlVP+fKibSf54/pOTv+dHt+nkL76MMIMEptYZ5pPBjPWNnBY2"
    "apyfFNDCtQHwwrLNKtwwqtNCgnh1UYKXXF3kEhNa1PgPxtYQaRSyaoiLt9J4wL4Q8/Xv0e"
    "100pdmM09oWyp0HCaf3fWpvCM4rkqF9+i6OxzR78UWQDeO5WMx+IgzHY38wRFqtDCJenlV"
    "JnJymfQNI4ETWpaA2LYtWzFJF/ADEmVXBqQU2wB43esDiFdO25+CPT+DHWocRw6bL+jlhL"
    "bhhJbnsNtm9TI5bH9DjmqBjLgSD2VsD2WAcHOUnwxmRLZZaRjEZeMZ8d51TBENGThfxIxA"
    "BpOfFMUvMKnBoxbtilrk51pzVl3Wnl9tcLRiDZ4MC2R023xOEFHhpGDvpOBXDh9N78ZjJr"
    "FdhA4WOCqajQIDvskdQm+SIwhgDM01rpLrjarU59WdHvX8H3nZE2PtAGpSrT5gXzcE2GcL"
    "/zQn7HaQKd2wqn02EtQ/jrcr/2yEh9yOOPjCQ26/otXzQm6p0NAzBTDYZlpZEYxgl62CEA"
    "atwmMYLYth+J92l013BvVbEcOoO83pqJadFQI2LJC3+DbQSOC9oCqtcnAHk7veSBJup1J/"
    "OBv6HtZm1maFVEQEuhcKnkrdUQJf3VEcaEAVw4ypomdZBgQoZ7qIaybQnhPVQ3XvjaReuH"
    "uTySjWv3vDZAe+u+lJ0xdnL+Ow8+XP7Xdiyriu2FrrasUdVCMqPGdYYgdVitceMoZycJ2G"
    "wVs2XxjtV7vvoBo9mSLx5qiwdWr7srMH3TTV65pZfCToswV8hFbhfKRlfCR71+iCpGqg0A"
    "pGUsNK1zWwgVkp7BtqHEfgl6dVnzet6rvtFS0g9glj8w5o8fSjh7ko8lAeSbPomS6KF2/K"
    "PtpF3GE0nZXJr57lJ1jPUhlWznzyoW8v8+FB+7ZZvcw6Wdep+rVvRIOz3e1s13X4t77buW"
    "6kU+1OdcNMzu5Et23HshyU5rJOmcFyg86aT3KpvTnHbRfHpTatekRIVGc/rv7zQnz4Q0Kg"
    "CfRKm41tFNrwBWctgQTHebDI1LgCTsaOVwVf7icVeeimHOK2lRcb2x4pCHRrjBMEHl2VIM"
    "HdTJp2BKp5j7qDm+G4IwDN1NEuhH/PO7vpjkLev/q3DBNsyy2HejVmloP5nCeWOdE+EqLN"
    "wyu/otX3sCYy7B7BcYm7M1f/RMaG2T6Xt8a/UImcF7Q7QtHDiVoJU7Cz9E9AFFyijfiEmf"
    "WfiA+1bNHJQeNDXTLc1JWYESHyS06KYkQgrMODRLW9iw8cJPoGbccfYGV5dUSllYy6DJ8j"
    "tQoYdYrT0UFVAWG/egvRPTstt2td0bZ1qX3rcg9aKzyoN+egtRoWmzzPyve9LSt51m+Mfv"
    "wPm2DSJw=="
)
