from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assignments', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='assignmentsubmission',
            old_name='file_path',
            new_name='submission_file',
        ),
        migrations.AlterField(
            model_name='assignmentsubmission',
            name='submission_file',
            field=models.FileField(upload_to='assignment_submissions/', blank=True, default='', max_length=500),
        ),
    ]
