from django.http import HttpResponseRedirect
from django.views.generic import View, ListView, CreateView, DetailView
from django.views.generic import UpdateView, DeleteView
from django.views.generic.base import RedirectView
from django.views.generic.edit import ProcessFormView, FormMixin
from django.db.models.loading import get_model
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied, ImproperlyConfigured
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from account.utils import user_display
from taggit.models import Tag
from voting.models import Vote

from items.models import Item, Content, Question, Link, Feature
from items.forms import QuestionForm, AnswerForm, ItemForm
from items.forms import LinkForm, FeatureForm
from profiles.models import Profile
from utils.votingtools import process_voting as _process_voting
from utils.followtools import process_following
from utils.asktools import process_asking
from utils.answertools import process_answering

import json

app_name = 'items'


class ContentView(View):

    def dispatch(self, request, *args, **kwargs):
        if 'model_name' in kwargs:
            self.model = get_model(app_name, kwargs['model_name'])
            form_class_name = self.model._meta.object_name + 'Form'
            if form_class_name in globals():
                self.form_class = globals()[form_class_name]
        return super(ContentView, self).dispatch(request, *args, **kwargs)


class ContentFormMixin(object):

    object = None

    def get(self, request, *args, **kwargs):
        if self.form_class:
            form = self.form_class(**{'request': request})
        else:
            form_class = self.get_form_class()
            form = self.get_form(form_class)
        return self.render_to_response(self.get_context_data(form=form))

    def load_form(self, request):
        if self.form_class and (
                    self.__class__ == ContentCreateView or self.model == Item):
            form_kwargs = self.get_form_kwargs()
            form_kwargs.update({"request": request})
            form = self.form_class(**form_kwargs)
        else:
            form_class = self.get_form_class()
            form = self.get_form(form_class)
        return form

    def post(self, request, *args, **kwargs):
        form = self.load_form(request)
        if "next" in request.POST:
            self.success_url = request.POST.get("next")
        if self.model == Item and "store_search" in request.POST:
            form.stores_search()
            return self.render_to_response(self.get_context_data(form=form))
        elif form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class ContentCreateView(ContentView, ContentFormMixin, CreateView):

    messages = {
        "object_created": {
            "level": messages.SUCCESS,
            "text": _("Thanks %(user)s, %(object)s successfully created.")
        },
        "creation_failed": {
            "level": messages.ERROR,
            "text": _("Warning %(user)s, %(object)s form is invalid.")
        },
    }

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ContentCreateView, self).dispatch(request,
                                                       *args,
                                                       **kwargs)

    def form_valid(self, form):
        self.object = form.save()
        messages.add_message(
            self.request, self.messages["object_created"]["level"],
            self.messages["object_created"]["text"] % {
                "user": user_display(self.request.user),
                "object": self.object._meta.verbose_name
            }
        )
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        messages.add_message(
            self.request, self.messages["creation_failed"]["level"],
            self.messages["creation_failed"]["text"] % {
                "user": user_display(self.request.user),
                "object": form._meta.model._meta.verbose_name
            }
        )
        return super(ContentCreateView, self).form_invalid(form)


class ContentUpdateView(ContentView, ContentFormMixin, UpdateView):

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(ContentUpdateView, self).dispatch(request,
                                                       *args,
                                                       **kwargs)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        kwargs = {"form": form}
        if "next" in request.GET:
            kwargs.update({"next": request.GET.get("next")})
        return self.render_to_response(self.get_context_data(**kwargs))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super(ContentUpdateView, self).post(request, *args, **kwargs)


class ContentDetailView(ContentView, DetailView, ProcessFormView, FormMixin):

    messages = {
        "object_created": {
            "level": messages.SUCCESS,
            "text": _("Thanks %(user)s, %(object)s successfully created.")
        },
        "creation_failed": {
            "level": messages.WARNING,
            "text": _("Warning %(user)s, %(object)s form is invalid.")
        },
    }

    def get_context_data(self, **kwargs):
        context = super(ContentDetailView, self).get_context_data(**kwargs)
        if self.model == Item:
            item = context["item"]

            feats = Feature.objects.filter(
                        Q(items__id=item.id) & Q(status=Content.STATUS.public)
            )

            questions = Question.objects.filter(
                Q(items__id=item.id) & Q(status=Content.STATUS.public)
            )

            POST_dict = self.request.POST.copy()

            if "question" in POST_dict:
                q_form = QuestionForm(POST_dict, request=self.request)
            else:
                q_form = QuestionForm(request=self.request)

            if "answer" in POST_dict and "question_id" in POST_dict:
                for q in questions:
                    if q.id != int(POST_dict["question_id"]):
                        q.answer_form = AnswerForm(request=self.request)
                    else:
                        q.answer_form = AnswerForm(POST_dict,
                                                        request=self.request)
            else:
                for q in questions:
                    q.answer_form = AnswerForm(request=self.request)

            sets = {
                "questions": questions,
                "links": Link.objects.filter(
                    Q(items__id=item.id) & Q(status=Content.STATUS.public)
                ),
                "feat_pos": feats.filter(positive=True),
                "feat_neg": feats.filter(positive=False)
            }

            for k in sets.keys():
                sets.update({k: sorted(list(sets[k]), key=lambda c:
                    Vote.objects.get_score(c)['score'], reverse=True)
                })

            sets.update({"feat_lists": [sets["feat_pos"], sets["feat_neg"]]})
            del sets["feat_pos"]
            del sets["feat_neg"]
            context.update(sets)

            prof_list = Profile.objects.filter(
                skills__id__in=self.object.tags.values_list('id', flat=True)
            ).distinct()
            context.update({"q_form": q_form, "prof_list": prof_list})
        elif self.model == Question:
            question = context["question"]
            question_list=list()
            #Build Related Questions List
            item=question.items.all()[0]
            question_list=list(Question.objects.filter(items=item))
            question_list.remove(question)
            list_quest=list(question.items.all())
            list_quest.remove(item)  
            for item_it in list_quest:
                question_list_it=list(Question.objects.filter(items=item_it))
                question_list_it.remove(question)
                if question_list_it:
                    question_list.append(question_list_it[0])
            context.update({
                'question_list': question_list
            })
            list_items = list(Item.objects.all().values_list('name', flat=True))
            item=question.items.all()[0]
            context.update({
                'prof_list_question': Profile.objects.filter(
                            skills__id__in=item.tags.values_list('id',
                            flat=True)).distinct()
            })                
            
            question = context.pop("question")

                    
            if "answer" in self.request.POST:
                question.answer_form = AnswerForm(self.request.POST,
                                                        request=self.request)
            else:
                question.answer_form = AnswerForm(request=self.request)
            context.update({"question": question})
            
            context.update({
                'data_source_items': json.dumps(list_items)
            })
            list_profiles = list(Profile.objects.all().values_list('name', flat=True))
            context.update({
                'data_source_profiles': json.dumps(list_profiles)
            })

        return context

    def form_invalid(self, form):
        self.object = self.get_object()
        messages.add_message(self.request,
            self.messages["creation_failed"]["level"],
            self.messages["creation_failed"]["text"] % {
                "user": user_display(self.request.user),
                "object": form._meta.model._meta.verbose_name
            }
        )
        return self.render_to_response(self.get_context_data(form=form))

    def form_valid(self, form, request, **kwargs):
        if form.cleaned_data:
            self.object = form.save(**kwargs)
            form.save_m2m()
            messages.add_message(self.request,
                self.messages["object_created"]["level"],
                self.messages["object_created"]["text"] % {
                    "user": user_display(self.request.user),
                    "object": self.object._meta.verbose_name
                }
            )
        if 'answer' in request.POST:
                return process_answering(request)
        else:   
            return HttpResponseRedirect(self.object.get_absolute_url())

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        if "vote_button" in request.POST:
            return self.process_voting(request)
#		elif "item_pick" in request.POST:
#            #Add a question to an other item
#            name = request.POST['item_pick']
#            item_list = Item.objects.filter(name=name)
#            item=item_list[0]
#            question_list=Question.objects.filter(pk=kwargs['pk'])
#            question=question_list[0]
#            question.items.add(item)
            
            response = item.get_absolute_url()
            return HttpResponseRedirect(response)
        elif "question" in request.POST:
            POST_dict = request.POST.copy()
            POST_dict.update(
                {'status': Content._meta.get_field('status').default}
            )
            form = QuestionForm(POST_dict, request=request)
            if form.is_valid():
                return self.form_valid(form, request, **kwargs)
            else:
                return self.form_invalid(form)
#		elif 'question_context' in request.POST:
#            form = QuestionForm_new(request.POST, request=request)
#            if form.is_valid():
#                return self.form_valid(form, request, **kwargs)
#            else:
#                return self.form_invalid(form)
        elif "answer" in request.POST:
            form = AnswerForm(request.POST, request=request)
            if form.is_valid():
                return self.form_valid(form, request, **kwargs)
            else:
                return self.form_invalid(form)
        elif "follow" in request.POST or "unfollow" in request.POST:
            return process_following(request, go_to_object=True)
        elif 'ask' or 'ask_prof_pick' in request.POST:
            return process_asking(request)
        else:
            return HttpResponseRedirect(request.path)

    @method_decorator(permission_required("profiles.can_vote",
                                          raise_exception=True))
    def process_voting(self, request):
        return _process_voting(request, go_to_object=True)


class ContentListView(ContentView, ListView, RedirectView):

    def get_queryset(self):
        if "tag_slug" in self.kwargs:
            self.tag = Tag.objects.get(slug=self.kwargs["tag_slug"])
            return Item.objects.filter(tags=self.tag)
        else:
            return super(ContentListView, self).get_queryset()

    def get_context_data(self, **kwargs):
        context = super(ContentListView, self).get_context_data(**kwargs)

        item=context["item_list"][0]
        questions = Question.objects.filter(
                        Q(items__id=item.id) & Q(status=Content.STATUS.public)
                    )
        context["question_list"]=questions

        if "item_list" in context:
            if hasattr(self, "tag"):
                context.update({"tag": self.tag})
                context["first_item"] = context["item_list"][0]

        if "sort_items" in self.request.POST:
            sort = "-pub_date"
            if self.request.POST["sort_items"] == "1":
                pass
            elif self.request.POST['sort_items'] == "2":
                sort = "pub_date"
            context["item_list"] = context["item_list"].order_by(sort)
            context["first_item"] = context["item_list"].order_by(sort)[0]

        if "template_choice" in self.request.POST:
            if self.request.POST["template_choice"] == "1":
                context["template_choice"] = 1
            else:
                context["template_choice"] = 2


        if "search" in self.request.GET:
            search_terms = self.request.GET.get("search", "")
            context["search_terms"] = search_terms
            if search_terms:
                self.template_name = "items/item_search.html"
                context["search_list"] = Item.objects.filter(
                                                name__icontains=search_terms
                )

        return context

    def post(self, request, *args, **kwargs):
        if "item_search" in request.POST:
            search = request.POST["item_search"]
            item_list = Item.objects.filter(name=search)
            if item_list.count() > 0:
                response = item_list[0].get_absolute_url()
            else:
                tag_list = Tag.objects.filter(name=search)
                if tag_list.count() > 0:
                    response = reverse("tagged_items",
                                        kwargs={'tag_slug': tag_list[0].slug}
                    )
                else:
                    response = "%s?search=%s" % (reverse("item_index"), search)
            return HttpResponseRedirect(response)
        else:
            return super(ContentListView, self).post(request, *args, **kwargs)


class ContentDeleteView(ContentView, DeleteView):

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not request.user.has_perm("can_manage", self.object):
            raise PermissionDenied
        success_url = self.get_success_url(request)
        self.object.delete()
        return HttpResponseRedirect(success_url)

    def get_success_url(self, request):
        if self.model.__name__ == "Item":
            success_url = reverse("item_index")
        elif "success_url" in request.GET:
            success_url = request.GET.get("success_url")
        else:
            success_url = None

        obj = self.object
        if success_url != obj.get_absolute_url() and success_url is not None:
            return success_url
        else:
            try:
                return obj.items.all()[0].get_absolute_url()
            except:
                pass
        raise ImproperlyConfigured
