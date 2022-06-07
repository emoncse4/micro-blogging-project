from django.shortcuts import render, get_object_or_404, redirect, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from blog.models import Post,Comment,Vote
from django.utils import timezone
from blog.forms import PostForm, CommentForm
from django.views.generic import (ListView,DetailView,CreateView,UpdateView,DeleteView)
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import F
from django.db.models import Q
# Create your views here.

class PostListView(ListView):
    model = Post

    def get_queryset(self):
        return Post.objects.filter(published_date__lte=timezone.now()).order_by('-published_date')

class PostDetailView(DetailView):
    model = Post

class CreatePostView(LoginRequiredMixin,CreateView):
    login_url = '/login/'
    redirect_field_name = 'blog/post_detail.html'

    form_class = PostForm

    model = Post


class PostUpdateView(LoginRequiredMixin,UpdateView):
    login_url = '/login/'
    redirect_field_name = 'blog/post_detail.html'

    form_class = PostForm

    model = Post

class PostDeleteView(LoginRequiredMixin,DeleteView):
    model = Post
    success_url = reverse_lazy('post_list')


def thumbs(request):
    if request.POST.get('action') == 'thumbs':

        id = int(request.POST.get('postid'))
        button = request.POST.get('button')
        update = Post.objects.get(id=id)

        if update.thumbs.filter(id=request.user.id).exists():

            q = Vote.objects.get(
                Q(post_id=id) & Q(user_id=request.user.id))
            evote = q.vote

            if evote == True:

                if button == 'thumbsup':

                    update.thumbsup = F('thumbsup') - 1
                    update.thumbs.remove(request.user)
                    update.save()
                    update.refresh_from_db()
                    up = update.thumbsup
                    down = update.thumbsdown
                    q.delete()
                    return JsonResponse({'up':up, 'down':down, 'remove':'none'})

                if button == 'thumbsdown':

                    update.thumbsup = F('thumbsup') - 1
                    update.thumbsdown = F('thumbsdown') + 1
                    update.save()
                    q.vote = False
                    q.save(update_fields=['vote'])
                    update.refresh_from_db()
                    up = update.thumbsup
                    down = update.thumbsdown
                    return JsonResponse({'up':up, 'down':down})
            pass

            if evote == False:

                if button == 'thumbsup':
                    update.thumbsup = F('thumbsup') + 1
                    update.thumbsdown = F('thumbsdown') - 1
                    update.save()
                    q.vote = True
                    q.save(update_fields['vote'])
                    update.refresh_from_db()
                    up = update.thumbsup
                    down = update.thumbsdown
                    return JsonResponse({'up':up, 'down':down})

                if button == 'thumbsdown':

                    update.thumbsdown = F('thumbsdown') - 1
                    update.thumbs.remove(request.user)
                    update.save()
                    update.refresh_from_db()
                    up = update.thumbsup
                    down = update.thumbsdown
                    q.delete()
                    return JsonResponse({'up':up, 'down':down, 'remove':'none'})

        else:
            if button == 'thumbsup':
                update.thumbsup = F('thumbsup') + 1
                update.thumbs.add(request.user)
                update.save()
                new = Vote(post_id=id, user_id=request.user.id, vote=True)
                new.save()
            else:
                update.thumbsdown = F('thumbsdown') + 1
                update.thumbs.add(request.user)
                update.save()
                new = Vote(post_id=id, user_id=request.user.id, vote=False)
                new.save()

            update.refresh_from_db()
            up = update.thumbsup
            down = update.thumbsdown

            return JsonResponse({'up':up, 'down':down})
    pass

@login_required
def post_publish(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.publish()
    return redirect('post_detail', pk=pk)

@login_required
def add_comment_to_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = CommentForm()
    return render(request, 'blog/comment_form.html', {'form': form})


@login_required
def comment_approve(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    comment.approve()
    return redirect('post_detail', pk=comment.post.pk)


@login_required
def comment_remove(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    post_pk = comment.post.pk
    comment.delete()
    return redirect('post_detail', pk=post_pk)
