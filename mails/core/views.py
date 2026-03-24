import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import Mail


# ---------- AUTH ----------

@csrf_exempt
@require_http_methods(["POST"])
def register_user(request):
    data = request.POST

    username = data.get("username")
    password = data.get("password")
    confirm = data.get("confirm_password")

    if not username or not password or not confirm:
        return JsonResponse({"error": "Missing fields"}, status=400)

    if password != confirm:
        return JsonResponse({"error": "Passwords do not match"}, status=400)

    if User.objects.filter(username=username).exists():
        return JsonResponse({"error": "Username already exists"}, status=400)

    User.objects.create_user(username=username, password=password)

    return JsonResponse({"status": "User created"}, status=201)


@csrf_exempt
@require_http_methods(["POST"])
def login_user(request):
    data = request.POST

    username = data.get("username")
    password = data.get("password")

    user = authenticate(request, username=username, password=password)

    if user is None:
        return JsonResponse({"error": "Invalid credentials"}, status=400)

    login(request, user)

    return JsonResponse({"status": "Logged in"})


@csrf_exempt
@require_http_methods(["POST"])
def logout_user(request):
    logout(request)
    return JsonResponse({"status": "Logged out"})


# ---------- MAIL ----------

@login_required
@require_http_methods(["GET"])
def open_inbox(request):
    mails = Mail.objects.filter(
        recipient=request.user,
        deleted_by_receiver=False
    ).order_by('-timestamp')

    data = [
        {
            "id": m.id,
            "from": m.sender.username,
            "message": m.message,
            "read": m.is_read,
            "time": str(m.timestamp)
        }
        for m in mails
    ]

    return JsonResponse({"inbox": data})


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def send_mail(request):
    receiver = request.POST.get("receiver")
    message = request.POST.get("message")

    if not receiver or not message:
        return JsonResponse({"error": "Missing fields"}, status=400)

    try:
        user = User.objects.get(username=receiver)
    except User.DoesNotExist:
        return JsonResponse({"error": "User not found"}, status=400)

    Mail.objects.create(
        sender=request.user,
        recipient=user,
        message=message
    )

    return JsonResponse({"status": "Sent"})


@login_required
@require_http_methods(["GET"])
def open_mail(request, mail_id):
    try:
        mail = Mail.objects.get(
            id=mail_id,
            recipient=request.user,
            deleted_by_receiver=False
        )
    except Mail.DoesNotExist:
        return JsonResponse({"error": "Not found"}, status=404)

    mail.is_read = True
    mail.save()

    return JsonResponse({
        "from": mail.sender.username,
        "message": mail.message,
        "time": str(mail.timestamp)
    })


@csrf_exempt
@login_required
@require_http_methods(["DELETE"])
def delete_mail(request, mail_id):
    try:
        mail = Mail.objects.get(id=mail_id)
    except Mail.DoesNotExist:
        return JsonResponse({"error": "Not found"}, status=404)

    if request.user == mail.recipient:
        mail.deleted_by_receiver = True
    elif request.user == mail.sender:
        mail.deleted_by_sender = True
    else:
        return JsonResponse({"error": "Not allowed"}, status=403)

    if mail.deleted_by_sender and mail.deleted_by_receiver:
        mail.delete()
    else:
        mail.save()

    return JsonResponse({"status": "Deleted"})


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def clear_inbox(request):
    Mail.objects.filter(recipient=request.user).update(deleted_by_receiver=True)
    return JsonResponse({"status": "Cleared"})


@login_required
@require_http_methods(["GET"])
def refresh_inbox(request):
    return open_inbox(request)