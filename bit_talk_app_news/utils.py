from profanity_filter import ProfanityFilter

from bit_talk_root.models import MongoUser
from .models import Comments, News_articles
from bit_talk_posts.models import Posts
from bson.objectid import ObjectId
import datetime
import firebase_admin
from firebase_admin import credentials, firestore


pf = ProfanityFilter()
cred = credentials.Certificate(
        "bit_talk_project/wm-notifications-firebase-adminsdk.json")
firebase_admin.initialize_app(cred)
"""
Generic methods to modify/update comments object
"""


def _push_to_firebase(news_id, comment_object):
    db = firestore.client()
    doc_ref = db.collection('news_comments').document(
        str(news_id))
    response = doc_ref.update({'comments': firestore.ArrayUnion(
        [{
            "comment_id": str(comment_object.id),
            "comment_text": "A",
            "time": "2022-02-03",
            "user_id": 23,
            "user_image": "link",
            "user_name": "Jack Link"}]
    )})
    # print(f"{response}")
    return response


def _add_comment(instance, raw_comment, user_ref):
    status_comment = 'New'
    if (pf.is_profane(raw_comment)):
        status_comment = 'Flagged'
    c = Comments(
        comment_text=pf.censor(raw_comment),
        status=status_comment,
        user_ref=user_ref,
        time_stamp=datetime.datetime.now)
    instance.comments.append(c)
    instance.no_of_comments += 1
    instance.save()
    # _push_to_firebase(instance.id, c)


def _report_comment(object_type, comment_id, reported_reason):

    if object_type == 'news':
        News_articles.objects(
        __raw__={'comments.id': ObjectId(comment_id)}  # noqa : E501
        ).update(
        __raw__={'$set': {'comments.$.reported_reason': reported_reason,  # noqa : E501
                          'comments.$.status': 'Reported',  # noqa : E501
                          'comments.$.reported_flag': True},
                 '$inc': {'comments.$.reported_count': 1}})  # noqa : E501

    if object_type == 'post':
        Posts.objects(
        __raw__={'comments.id': ObjectId(comment_id)}  # noqa : E501
        ).update(
        __raw__={'$set': {'comments.$.reported_reason': reported_reason,  # noqa : E501
                          'comments.$.status': 'Reported',  # noqa : E501
                          'comments.$.reported_flag': True},
                 '$inc': {'comments.$.reported_count': 1}})  # noqa : E501


def _add_like(instance, user_id):

    user = MongoUser.objects.get(id=user_id)
    if user not in instance.liked_by:
        instance.liked_by.append(user)
        instance.no_of_likes += 1
        instance.save()


def _update_comment_status(object_type, comment_id, comment_status):

    if object_type == 'news':
        News_articles.objects(
                __raw__={'comments.id': ObjectId(comment_id)}  # noqa : E501
                ).update(
                __raw__={'$set': {'comments.$.status': comment_status}})  # noqa : E501

    if object_type == 'post':
        Posts.objects(
                __raw__={'comments.id': ObjectId(comment_id)}  # noqa : E501
                ).update(
                __raw__={'$set': {'comments.$.status': comment_status}})  # noqa : E501


def _approve_comment(object_type, comment_id, comment_status):

    if object_type == 'news':

        News_articles.objects(
                __raw__={'comments.id': ObjectId(comment_id)}  # noqa : E501
                ).update(
                __raw__={'$set': {'comments.$.status': comment_status,
                                  'comments.$.reported_flag': True,
                                  'comments.$.reported_count': 0,
                                  'comments.$.reported_reason': ""
                                  }})

    if object_type == 'post':
        Posts.objects(
                __raw__={'comments.id': ObjectId(comment_id)}  # noqa : E501
                ).update(
                __raw__={'$set': {'comments.$.status': comment_status,
                                  'comments.$.reported_flag': True,
                                  'comments.$.reported_count': 0,
                                  'comments.$.reported_reason': ""
                                  }})
