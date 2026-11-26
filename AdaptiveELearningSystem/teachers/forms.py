from pathlib import Path

from django import forms

from courses.models import LearningMaterial
from .models import TeacherProfile


class LearningMaterialUploadForm(forms.ModelForm):
    message_text = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Send a short message to enrolled students about this material.'}))

    class Meta:
        model = LearningMaterial
        fields = ['course', 'title', 'material_type', 'file_path', 'note_text']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'material_type': forms.Select(attrs={'class': 'form-select'}),
            'file_path': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.mp4,.mov,.avi,.webm',
            }),
            'note_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Add teacher notes for this course material.'}),
        }

    def __init__(self, *args, **kwargs):
        teacher_profile = kwargs.pop('teacher_profile', None)
        super().__init__(*args, **kwargs)
        self.fields['course'].queryset = teacher_profile.courses.all() if teacher_profile else self.fields['course'].queryset.none()
        self.fields['material_type'].choices = LearningMaterial.MATERIAL_TYPES

    def clean(self):
        cleaned_data = super().clean()
        material_type = cleaned_data.get('material_type')
        uploaded_file = cleaned_data.get('file_path')
        note_text = cleaned_data.get('note_text')

        if material_type == 'note':
            if not note_text:
                self.add_error('note_text', 'Enter note text for note materials.')
            if uploaded_file:
                self.add_error('file_path', 'Notes should not include a file attachment.')
        else:
            if not uploaded_file:
                self.add_error('file_path', 'A file is required for this material type.')
            elif uploaded_file:
                extension = Path(uploaded_file.name).suffix.lower()
                allowed_extensions = {'.pdf', '.doc', '.docx', '.mp4', '.mov', '.avi', '.webm'}
                if material_type == 'video':
                    allowed_extensions = {'.mp4', '.mov', '.avi', '.webm'}
                elif material_type in {'pdf', 'doc'}:
                    allowed_extensions = {'.pdf', '.doc', '.docx'}
                if extension not in allowed_extensions:
                    self.add_error('file_path', 'Only PDF, DOC, DOCX, MP4, MOV, AVI, and WEBM files are allowed.')
            if note_text:
                self.add_error('note_text', 'Only note materials may include note text.')

        return cleaned_data


class TeacherProfileForm(forms.ModelForm):
    class Meta:
        model = TeacherProfile
        fields = ['subject_specialization', 'qualification', 'phone_number', 'bio', 'profile_picture']
        widgets = {
            'subject_specialization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Mathematics'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. M.Ed.'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mobile number'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'A short bio about your teaching style...'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
