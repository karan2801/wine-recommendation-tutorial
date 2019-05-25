from django.shortcuts import get_object_or_404,render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Wine, Review,Cluster
from .forms import ReviewForm
import datetime
from django.contrib.auth.decorators import login_required
from .suggestions import update_clusters

def review_list(request):
	latest_review_list = Review.objects.order_by('-pub_date')[:9]
	context = {'latest_review_list':latest_review_list}
	return render(request,'reviews/review_list.html',context)

def review_detail(request,review_id):
	review = get_object_or_404(Review, pk=review_id)
	return render(request,'reviews/review_detail.html',{'review':review})

def wine_list(request):
	wine_list = Wine.objects.order_by('-name')[:9]
	context = {'wine_list':wine_list}
	return render(request,'reviews/wine_list.html',context)

def wine_detail(request,wine_id):
	wine = get_object_or_404(Wine, pk=wine_id)
	return render(request,'reviews/wine_detail.html',{'wine':wine})

@login_required
def add_review(request,wine_id):
	wine = get_object_or_404(Wine, pk=wine_id)
	form = ReviewForm(request.POST)
	if form.is_valid():
		rating = form.cleaned_data['rating']
		comment = form.cleaned_data['comment']
		#user_name = form.cleaned_data['user_name']
		user_name = request.user.username
		review = Review()
		review.wine = wine
		review.user_name = user_name
		review.rating = rating
		review.comment = comment
		review.pub_date = datetime.datetime.now()
		review.save()
		update_clusters()
		return HttpResponseRedirect(reverse('reviews:wine_detail',args=(wine.id,)))
	return render(request,'reviews/wine_detail.html',{'wine':wine,'form':form})


def user_review_list(request, username=None):
    if not username:
        username = request.user.username
    latest_review_list = Review.objects.filter(user_name=username).order_by('-pub_date')
    context = {'latest_review_list':latest_review_list, 'username':username}
    return render(request, 'reviews/user_review_list.html', context)

@login_required
def user_recommendation_list(request):
    user_reviews = Review.objects.filter(user_name=request.user.username).prefetch_related('wine')
    user_reviews_wine_ids = set(map(lambda x: x.wine.id, user_reviews))
    try:
        user_cluster_name = \
            User.objects.get(username=request.user.username).cluster_set.first().name
    except: # if no cluster has been assigned for a user, update clusters
        update_clusters()
        user_cluster_name = \
            User.objects.get(username=request.user.username).cluster_set.first().name
    
    user_cluster_other_members = Cluster.objects.get(name=user_cluster_name).users.exclude(username=request.user.username).all()
    other_members_usernames = set(map(lambda x: x.username, user_cluster_other_members))
    other_users_reviews = Review.objects.filter(user_name__in=other_members_usernames).exclude(wine__id__in=user_reviews_wine_ids)
    other_users_reviews_wine_ids = set(map(lambda x: x.wine.id, other_users_reviews))
    wine_list = sorted(
    	list(Wine.objects.filter(id__in=other_users_reviews_wine_ids)),
    	key=lambda x: x.average_rating(),
    	reverse=True
    )

    return render(request, 'reviews/user_recommendation_list.html', {'username': request.user.username,'wine_list': wine_list})


# Create your views here.
