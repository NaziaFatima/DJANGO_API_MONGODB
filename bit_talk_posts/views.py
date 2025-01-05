from rest_framework_mongoengine.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from .serializers import PostsSerializer
from .models import Posts
from bit_talk_app_news.utils import (
        _add_comment,
        _report_comment,
        _add_like,
        _update_comment_status,
        _approve_comment
        )
from bit_talk_app_news.models import STATUS_CHOICES


class PostsViewSet(ModelViewSet):
    # permission_classes = (IsAuthenticated,)

    serializer_class = PostsSerializer

    def get_queryset(self):
        return Posts.objects.all()

    @action(detail=True, methods=['patch'], url_path=r'comments',)
    def add_comment(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = PostsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.validated_data['comments']
        for comment in serializer.validated_data['comments']:
            raw_comment = comment['comment_text']
            try:
                _add_comment(instance, raw_comment, comment['user_ref'])
            except Exception as err:
                return Response({' Error message': str(err)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'Added comment succefully!'})

    @action(detail=True, methods=['patch'],
            url_path=r'report_comment/(?P<comment_id>[^/.]+)')
    def report_comment(self, request, *args, **kwargs):
        reported_reason = request.data.get('reported_reason')
        if reported_reason is None:
            return Response({'message': '\'reported_reason\' is missing!'},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            _report_comment('post', kwargs['comment_id'], reported_reason)
        except Exception as e:
            return Response({'message': str(e)},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'Comment reported!'},
                        status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'],
            url_path=r'update_comment_status/(?P<comment_id>[^/.]+)')
    def update_comment_status(self, request, *args, **kwargs):
        comment_status = request.data.get('status')
        try:
            if comment_status in dict(STATUS_CHOICES):
                if comment_status == 'Approved':
                    _approve_comment('post', kwargs['comment_id'], comment_status)
                _update_comment_status('post', kwargs['comment_id'], comment_status)
            else:
                return Response({'message': 'Invalid status!'},
                                status=status.HTTP_400_BAD_REQUEST)
        except ValueError as err:
            return Response({'message': str(err)},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'Status updated!'},
                        status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch'],
            url_path=r'like/(?P<user_id>[^/.]+)')
    def add_like(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
                            instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        _add_like(instance, kwargs['user_id'])
        return Response(serializer.data)
