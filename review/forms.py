"""Forms for the ``review`` app."""
from django import forms
from django.conf import settings
from django.utils.translation import get_language

from .models import Review, Rating, RatingCategory


class ReviewForm(forms.ModelForm):
    def __init__(self, reviewed_item, user=None, *args, **kwargs):
        self.user = user
        self.reviewed_item = reviewed_item
        super(ReviewForm, self).__init__(*args, **kwargs)
        # Dynamically add fields for each rating category
        for category in RatingCategory.objects.all():
            self.fields['category_{}'.format(category.pk)] = forms.ChoiceField(
                choices=getattr(settings, 'REVIEW_RATING_CHOICES',
                                Rating.rating_choices),
                label=category.get_translation().name,
            )
            if self.instance.pk:
                try:
                    self.initial.update({
                        'category_{}'.format(category.pk): Rating.objects.get(
                            review=self.instance, category=category).value,
                    })
                except Rating.DoesNotExist:
                    pass

    def save(self, *args, **kwargs):
        if not self.instance.pk:
            self.instance.user = self.user
            self.instance.reviewed_item = self.reviewed_item
            self.instance.language = get_language()
        self.instance = super(ReviewForm, self).save(*args, **kwargs)
        # Update or create ratings
        for field in self.fields:
            if field.startswith('category_'):
                rating, created = Rating.objects.get_or_create(
                    review=self.instance,
                    category=RatingCategory.objects.get(
                        pk=field.replace('category_', '')),
                )
                rating.value = self.cleaned_data[field]
                rating.save()
        return self.instance

    class Meta:
        model = Review
        fields = ('content', )
