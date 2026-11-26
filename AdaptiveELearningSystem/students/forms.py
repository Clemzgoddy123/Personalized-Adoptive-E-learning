from django import forms

from .models import StudentProfile


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['class_level', 'guardian_contact', 'phone_number', 'bio', 'profile_picture']
        widgets = {
            'class_level': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Grade 10'}),
            'guardian_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Guardian name and phone'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Mobile number'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell us a little about yourself...'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
