import yaml
from django.contrib.auth import login, authenticate
from django.db.models import F, Sum
from django.http import JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import User, Contact, Shop, Category, Product, \
    ProductInfo, Parameter, ProductParameter, Order
from .permissions import IsShop
from .serializers import ShopSerializer, CategorySerializer, \
    ProductSerializer, OrderSerializer, OrderInfoSerializer, \
    OrderItemSerializer
# from .tools import send_registration_confirmation, send_order_confirmation


class UserRegisterView(APIView):
    """
    Класс для регистрации пользователей
    """

    def post(self, request, *args, **kwargs):
        user = User.objects.create(email=request.data['email'],
                                   password=request.data['password'],
                                   username=request.data['username'],
                                   full_name=request.data['full_name'],
                                   type=request.data['type'],
                                   company=request.data['company'],
                                   position=request.data['position'])
        user.set_password(request.data['password'])
        user.save()
        # send_registration_confirmation(request.user.id)
        return JsonResponse({'Status': True})


class Login(APIView):
    """
    Класс для выполнения входа пользователем в систему
    """

    def post(self, request, *args, **kwargs):
        user = authenticate(request, username=request.data['username'],
                            password=request.data['password'])
        if user is not None:
            if user.is_active:
                login(request, user)
                return JsonResponse({'status': True,
                                     'you are now logged in as':
                                         request.user.username})
        else:
            return JsonResponse({'status': 'invalid data'})


class ContactView(APIView):
    """
    Класс для заполнения контактной информации о пользователе
    """
    def post(self, request, *args, **kwargs):
        contact = Contact.objects.create(user=request.user,
                                         city=request.data['city'],
                                         street=request.data['street'],
                                         house=request.data['house'],
                                         structure=request.data['structure'],
                                         building=request.data['building'],
                                         apartment=request.data['apartment'],
                                         phone=request.data['phone'])
        contact.save()
        return JsonResponse({'status': 'success'})


class SupplierUpdate(APIView):
    """
    Класс для загрузки товаров
    """
    permission_classes = [IsAuthenticated & IsShop]

    def post(self, request, file_name):
        with open(f'data/{file_name}', 'r', encoding='UTF-8') as stream:
            data = yaml.safe_load(stream)
            shop, created = Shop.objects.get_or_create(name=data['shop'])
            for category in data['categories']:
                category_object, created = Category.objects.get_or_create(
                    id=category['id'], name=category['name'])
                category_object.shops.add(shop.id)
                category_object.save()
            for product in data['goods']:
                product_object, created = Product.objects.get_or_create(
                    name=product['name'],
                    category_id=product['category'])
                product_info = ProductInfo.objects.create(
                    product_id=product_object.id,
                    shop_id=shop.id,
                    external_id=product['id'],
                    model=product['model'],
                    quantity=product['quantity'],
                    price=product['price'],
                    price_rrc=product['price_rrc']
                )
                for key, value in product['parameters'].items():
                    parameter_object, created = \
                        Parameter.objects.get_or_create(name=key)
                    ProductParameter.objects.create(
                        product_info_id=product_info.id,
                        parameter_id=parameter_object.id,
                        value=value)
        return JsonResponse({'status': 'products added successfully'})


class ShopView(ReadOnlyModelViewSet):
    """
    Класс для просмотра всех магазинов и сортировки по параметру "статус"
    """
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    permission_classes = [IsAuthenticated]
    filterset_backends = [DjangoFilterBackend]
    filterset_fields = ['state']


class CategoryView(ReadOnlyModelViewSet):
    """
    Класс для просмотра всех категорий товаров и сортировки по параметру
    "магазины"
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    filterset_backends = [DjangoFilterBackend]
    filterset_fields = ['shops']


class ProductView(ReadOnlyModelViewSet):
    """
    Класс для просмотра всех товаров и сортировки по параметру "категория"
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filterset_backends = [DjangoFilterBackend]
    filterset_fields = ['category']


class OrderView(APIView):
    """
    Класс для получения всех заказов, созданных пользователем, и создания
    нового заказа
    """

    def get(self, request, *args, **kwargs):
        permission_classes = [IsAuthenticated]
        orders = Order.objects.filter(user_id=request.user.id).exclude(
            state='basket').annotate(total_sum=Sum(
            F('order_items__quantity') * F(
                'order_items__product_info__price')))
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        order = Order.objects.create(user=request.user,
                                     state='basket')
        for order_item in request.data:
            order_item.update({'order': order.id})
            serializer = OrderItemSerializer(data=order_item)
            if serializer.is_valid():
                serializer.save()
            else:
                return JsonResponse(
                    {'Status': False, 'Errors': serializer.errors})
        return JsonResponse({'Status': True})


class OrderInfoView(APIView):
    """
    Класс для просмотра подробной информации о заказе
    """

    def get(self, request, order_id, *args, **kwargs):
        permission_classes = [IsAuthenticated]
        order = Order.objects.filter(id=order_id).annotate(total_sum=Sum(
            F('order_items__quantity') * F(
                'order_items__product_info__price')))
        serializer = OrderInfoSerializer(order, many=True)
        return Response(serializer.data)


class BasketView(APIView):
    """
    Класс для заполнения контактов в корзине
    """

    def patch(self, request, *args, **kwargs):
        permission_classes = [IsAuthenticated]
        contact = Contact.objects.get(id=request.data['contacts'])
        order = Order.objects.get(user_id=request.user.id, state='basket')
        order.contact = contact
        order.state = 'new'
        order.save()
        return JsonResponse({'Status': True})
        # return redirect("order_confirmation")


class OrderConfirmation(APIView):
    """
    Класс для подтверждения заказа
    """

    def post(self, request, *args, **kwargs):
        permission_classes = [IsAuthenticated]
        order = Order.objects.get(user_id=request.user.id, state='new')
        action = request.data['action']
        if action == 'approve':
            order.state = 'confirmed'
            order.save()
            # send_order_confirmation(request.user.id)
            return JsonResponse({'Status': True})
            # return redirect("order_confirmed")
        elif action == 'disapprove':
            return JsonResponse({'Status': 'Now you can change your order'})
            # return redirect("basket")
