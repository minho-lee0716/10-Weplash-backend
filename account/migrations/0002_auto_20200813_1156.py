# Generated by Django 3.0.7 on 2020-08-13 02:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('photo', '0001_initial'),
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userinterest',
            name='interest',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='photo.HashTag'),
        ),
        migrations.AddField(
            model_name='userinterest',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='account.User'),
        ),
        migrations.AddField(
            model_name='user',
            name='following',
            field=models.ManyToManyField(related_name='_user_following_+', through='account.Follow', to='account.User'),
        ),
        migrations.AddField(
            model_name='user',
            name='interest',
            field=models.ManyToManyField(through='account.UserInterest', to='photo.HashTag'),
        ),
        migrations.AddField(
            model_name='user',
            name='like',
            field=models.ManyToManyField(related_name='like_photo', through='account.Like', to='photo.Photo'),
        ),
        migrations.AddField(
            model_name='like',
            name='photo',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='photo.Photo'),
        ),
        migrations.AddField(
            model_name='like',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='like_user', to='account.User'),
        ),
        migrations.AddField(
            model_name='follow',
            name='from_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='followee', to='account.User'),
        ),
        migrations.AddField(
            model_name='follow',
            name='to_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='follower', to='account.User'),
        ),
        migrations.AddField(
            model_name='collection',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='collection', to='account.User'),
        ),
    ]
