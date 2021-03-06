from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.template import Context
from django.template.loader import get_template
from django.utils.translation import ugettext_lazy as _
from django.utils import translation

from account.utils import user_display

from utils.tools import unescape


def send_mail(subject, subject_kwargs, receiver, txt_template, html_template,
              context, sender):
    translation.activate(receiver.account.language)
    subject = subject % subject_kwargs
    msg_txt = txt_template.render(context)
    msg_html = html_template.render(context)

    email = receiver.email if not settings.DEBUG else sender.email
    newco = '"NewCo" <notifications@newco-project.fr>'
    msg = EmailMultiAlternatives(unescape(subject), msg_txt, newco, [email])
    msg.attach_alternative(msg_html, "text/html")

#    waiting_time = datetime.timedelta(minutes=1)
#    last_mail, created = LastMail.objects.get_or_create(user=receiver)
#    diff = timezone.now() - last_mail.modified
#    if diff > waiting_time or created:
#        last_mail.save()
    msg.send()
    translation.deactivate()


def mail_question_author(request, answer):
    question = answer.question
    receiver = question.author
    receiver_name = user_display(question.author)
    answerer = answer.author
    answerer_name = user_display(answer.author)

    subject = _("%(receiver)s, %(answerer)s has answered your question!")
    subject_kwargs = {"receiver": receiver_name, "answerer": answerer_name}

    txt_template = get_template("mail/_answer_notification_email.txt")
    html_template = get_template("mail/_answer_notification_email.html")

    context = Context({
        "answer": answer,
        "request": request,
        "receiver": receiver_name,
        "receiver_url": request.build_absolute_uri(receiver.get_absolute_url()),
        "answerer": answerer_name,
        "answerer_url": request.build_absolute_uri(answerer.get_absolute_url()),
        "message_subject": subject,
    })
    send_mail(subject, subject_kwargs, receiver, txt_template, html_template,
              context, answerer)


def mail_helper(request, receiver, requester, question, receiver_name=None,
                requester_name=None):
    if not receiver_name:
        receiver_name = user_display(receiver)
    if not requester_name:
        requester_name = user_display(requester)

    subject = _("%(receiver)s, %(requester)s needs your help.")
    subject_kwargs = {"receiver": receiver_name, "requester": requester_name}

    txt_template = get_template("mail/_ask_notification_email.txt")
    html_template = get_template("mail/_ask_notification_email.html")

    context = Context({
        "receiver": receiver_name,
        "receiver_url": request.build_absolute_uri(receiver.get_absolute_url()),
        "asker": requester_name,
        "asker_url": request.build_absolute_uri(requester.get_absolute_url()),
        "request": request,
        "message_subject": subject,
        "question": question,
        "question_url": request.build_absolute_uri(
            question.get_absolute_url()),
        "settings_url": request.build_absolute_uri(reverse("account_settings"))
    })

    send_mail(subject, subject_kwargs, receiver, txt_template, html_template,
              context, requester)


def mail_followee(request, fwee, fwer):
    followee_name = user_display(fwee)
    follower_name = user_display(fwer)

    subject = _("%(followee)s, %(follower)s is now following you on NewCo.")
    subject_kwargs = {"followee": followee_name, "follower": follower_name}

    txt_template = get_template("mail/_follow_notification_email.txt")
    html_template = get_template("mail/_follow_notification_email.html")

    context = Context({
        "followee": fwee,
        "follower": fwer,
        "followee_name": followee_name,
        "follower_name": follower_name,
        "followee_url": request.build_absolute_uri(fwee.get_absolute_url()),
        "follower_url": request.build_absolute_uri(fwer.get_absolute_url()),
        "request": request,
        "message_subject": subject
    })

    send_mail(subject, subject_kwargs, fwee, txt_template, html_template,
              context, fwer)
