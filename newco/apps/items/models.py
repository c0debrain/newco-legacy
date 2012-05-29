from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from taggit.managers import TaggableManager
from django.db.models import permalink
from django.db import transaction
from django.template.defaultfilters import slugify
from django.forms import ModelForm
import datetime
from django.forms.widgets import Textarea
from django.shortcuts import get_object_or_404

class CannotManage(Exception): pass

class Content(models.Model):

    def user_can_manage_me(self, user):
        try:
            if user == self.author:
                return user == self.author or user.is_superuser
        except AttributeError:
            pass
        return user.is_superuser
    
    class Meta:
        abstract = True

class Item(Content):
    name = models.CharField(max_length=255, verbose_name=_('Name'))
    slug = models.SlugField(verbose_name=_('Slug'), editable=False)
    last_modified = models.DateTimeField(auto_now=True,
                                         verbose_name=_('Last modified'))
    tags = TaggableManager()
    
    def save(self):
        self.slug = slugify(self.name)
        super(Item, self).save()

    class Meta:
             pass
             
    def __unicode__(self):
        return u'%s' % (self.name)
    
    @permalink
    def get_absolute_url(self):
            return ('item_detail', None, {"model_name":"item","pk": self.id,"slug": self.slug} )

class Question(Content):
    content = models.CharField(max_length=200)
    pub_date = models.DateTimeField(default=datetime.datetime.today(),
                                    editable=False,
                                    verbose_name=_('date published'))
    author = models.ForeignKey(User)
    items = models.ManyToManyField(Item)
    
    def __unicode__(self):
        return u'%s' % (self.content)
    
    @permalink
    def get_absolute_url(self):
            return ('item_detail', None, {"model_name":"item","pk": self.items.all()[0].id,"slug": self.items.all()[0].slug} )

class Answer(Content):
    question = models.ForeignKey(Question)
    content = models.CharField(max_length=1000)
    pub_date = models.DateTimeField(default=datetime.datetime.today(),
                                    editable=False,
                                    verbose_name=_('date published'))
    author = models.ForeignKey(User)
    
    @permalink
    def get_absolute_url(self):
            return ('item_detail', None, {"model_name":"item","pk": self.question.items.all()[0].id,"slug": self.question.items.all()[0].slug} )

class Story(models.Model):
    title = models.CharField(max_length=200)
    content = models.CharField(max_length=2000)
    items = models.ManyToManyField(Item)
    
class QuestionForm(ModelForm):

    create = False

    def __init__(self, *args, **kwargs):
        if 'instance' not in kwargs or kwargs['instance'] == None:
            self.create = True
            self.request = kwargs.pop('request')
            self.user = self.request.user
        return super(QuestionForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Question
        exclude = ('author', 'items')
        widgets = {
            'content': Textarea(attrs={'class': 'span4', 'placeholder': 'Ask something specific. Be concise.', 'rows': 1}),
        }

    def save(self, commit=True, **kwargs):
        if commit and self.create:
            question = super(QuestionForm, self).save(commit=False)
            question.author = self.user
            question.save()
            question.items.add(kwargs.pop('pk'))
        else:
            return super(QuestionForm, self).save(commit)

class AnswerForm(ModelForm):

    create = False

    def __init__(self, *args, **kwargs):
        if 'instance' not in kwargs or kwargs['instance'] == None:
            self.create = True
            self.request = kwargs.pop('request')
            self.user = self.request.user
            self.question_id = self.request.REQUEST['question_id']
            self.question = Question.objects.get(pk=self.question_id)
        return super(AnswerForm, self).__init__(*args, **kwargs)
    
    class Meta:
        model = Answer
        fields = ('content', )
        widgets = {
            'content': Textarea(attrs={'class': 'span6', 'placeholder': 'Be concise and to the point.', 'rows': 6}),
        }
      
    @transaction.commit_manually  
    def save(self, commit=True, **kwargs):
        if commit and self.create:
            answer = super(AnswerForm, self).save(commit=False)
            answer.author = self.user
            answer.question = self.question
            answer.save()
            transaction.commit()
            return answer
        else:
            return super(AnswerForm, self).save(commit)

class StoryForm(ModelForm):
    class Meta:
        model = Story
