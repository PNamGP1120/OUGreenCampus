# OUGreenApp/serializers.py
from rest_framework import serializers

from OUGreenApp.models import User, Category, News, ProjectContest, Proposal, Document, Feedback, AIUsageLog, Comment, \
    Like, NewsletterSubscriber


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role', 'phone', 'first_name', 'last_name', 'avatar', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        data = validated_data.copy()
        user = User(**data)
        user.set_password(data['password'])
        user.save()
        return user

    def to_representation(self, user):
        rep = super().to_representation(user)
        rep['avatar'] = user.avatar.url if user.avatar else None
        return rep

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'created_at', 'updated_at')
        read_only_fields = ('slug',)


class NewsSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        slug_field='slug',
        queryset=Category.objects.all()
    )
    author = serializers.ReadOnlyField(source='author.username')
    tags = serializers.StringRelatedField(many=True)

    class Meta:
        model = News
        fields = (
            'id', 'title', 'content', 'image', 'category',
            'tags', 'author', 'created_at', 'updated_at'
        )
        read_only_fields = ('author', 'created_at', 'updated_at')

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        tags_data = validated_data.pop('tags', [])
        news = News.objects.create(**validated_data)
        news.tags.set(tags_data)
        return news

    def update(self, instance, validated_data):
        if 'tags' in validated_data:
            tags_data = validated_data.pop('tags')
            instance.tags.set(tags_data)
        return super().update(instance, validated_data)


class ProjectContestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectContest
        fields = (
            'id', 'title', 'description', 'status',
            'start_date', 'end_date', 'created_at', 'updated_at'
        )


class ProposalSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Proposal
        fields = (
            'id', 'project_contest', 'user', 'content', 'status',
            'created_at', 'updated_at'
        )
        read_only_fields = ('user', 'created_at', 'updated_at')

class DocumentSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Document
        fields = (
            'id', 'title', 'description', 'file', 'user', 'tags',
            'created_at', 'updated_at'
        )
        read_only_fields = ('user', 'created_at', 'updated_at')

    def to_representation(self, document):
        rep = super().to_representation(document)
        rep['file'] = document.file.url if document.file else None
        return rep


class FeedbackSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Feedback
        fields = ('id', 'user', 'message', 'created_at')
        read_only_fields = ('user', 'created_at')


class AIUsageLogSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = AIUsageLog
        fields = ('id', 'user', 'type', 'input_data', 'output_data', 'created_at')
        read_only_fields = ('user', 'created_at'    )


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'content', 'user', 'news', 'project', 'created_at']
        read_only_fields = ['user', 'created_at']

class LikeSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Like
        fields = ['id', 'user', 'news', 'project', 'created_at']
        read_only_fields = ['user', 'created_at']


class WasteClassifySerializer(serializers.Serializer):
    image = serializers.ImageField(required=True)

    def validate_image(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Ảnh quá lớn, vui lòng chọn ảnh dưới 5MB.")
        return value


class NewsletterSubscriberSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsletterSubscriber
        fields = ["id", "email", "created_at"]
