from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("quizapp", "0006_quizsession_quiz_started_at"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[],
            database_operations=[
                migrations.RunSQL(
                    sql="""
                        ALTER TABLE "quizapp_question"
                        DROP COLUMN IF EXISTS "video_url";

                        ALTER TABLE "quizapp_question"
                        DROP COLUMN IF EXISTS "video_file";
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
        ),
    ]