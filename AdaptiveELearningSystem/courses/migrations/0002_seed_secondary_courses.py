from django.db import migrations


def create_secondary_courses(apps, schema_editor):
    Course = apps.get_model('courses', 'Course')
    TeacherProfile = apps.get_model('teachers', 'TeacherProfile')

    teacher_profiles = list(TeacherProfile.objects.all())
    if not teacher_profiles:
        return

    sample_courses = [
        {
            'title': 'Secondary Mathematics',
            'description': 'A comprehensive secondary mathematics course covering algebra, geometry, and data handling.',
            'subject': 'Mathematics',
            'class_level': 'Form 1',
        },
        {
            'title': 'English Language & Literature',
            'description': 'Develop reading, writing, and analysis skills through prose, poetry, and practical composition.',
            'subject': 'English',
            'class_level': 'Form 1',
        },
        {
            'title': 'Biology Foundations',
            'description': 'Explore cell biology, ecology, and human systems tailored for secondary learners.',
            'subject': 'Biology',
            'class_level': 'Form 2',
        },
        {
            'title': 'Chemistry Concepts',
            'description': 'Introduction to chemical reactions, atomic structure, and periodic trends for secondary science class.',
            'subject': 'Chemistry',
            'class_level': 'Form 2',
        },
        {
            'title': 'Physics Essentials',
            'description': 'Learn the fundamentals of motion, energy, forces, and waves in a secondary physics course.',
            'subject': 'Physics',
            'class_level': 'Form 3',
        },
        {
            'title': 'World History',
            'description': 'Investigate key historical events, cultures, and movements from ancient times to the modern era.',
            'subject': 'History',
            'class_level': 'Form 3',
        },
        {
            'title': 'Geography and Environmental Studies',
            'description': 'Study physical geography, maps, climate systems, and sustainable development.',
            'subject': 'Geography',
            'class_level': 'Form 1',
        },
        {
            'title': 'Introductory Computer Science',
            'description': 'Build problem-solving skills with basic programming, logic, and computer systems concepts.',
            'subject': 'Computer Science',
            'class_level': 'Form 2',
        },
    ]

    for index, course_data in enumerate(sample_courses):
        teacher = teacher_profiles[index % len(teacher_profiles)]
        Course.objects.get_or_create(
            title=course_data['title'],
            defaults={
                'description': course_data['description'],
                'subject': course_data['subject'],
                'class_level': course_data['class_level'],
                'teacher': teacher,
            },
        )


def remove_secondary_courses(apps, schema_editor):
    Course = apps.get_model('courses', 'Course')
    titles = [
        'Secondary Mathematics',
        'English Language & Literature',
        'Biology Foundations',
        'Chemistry Concepts',
        'Physics Essentials',
        'World History',
        'Geography and Environmental Studies',
        'Introductory Computer Science',
    ]
    Course.objects.filter(title__in=titles).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_secondary_courses, remove_secondary_courses),
    ]
