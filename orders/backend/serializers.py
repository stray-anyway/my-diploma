from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, StringRelatedField

from .models import Shop, Category, Product, ProductParameter, \
    ProductInfo, Order, Contact, OrderItem, User


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'full_name']
        read_only_fields = ['id']


class ShopSerializer(ModelSerializer):
    class Meta:
        model = Shop
        fields = ['id', 'name', 'state']
        read_only_fields = ['id']


class CategorySerializer(ModelSerializer):
    shops = StringRelatedField(many=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'shops']
        read_only_fields = ['id']


class ProductSerializer(ModelSerializer):
    category = StringRelatedField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'category']
        read_only_fields = ['id']


class ProductParameterSerializer(ModelSerializer):
    parameter = StringRelatedField()

    class Meta:
        model = ProductParameter
        fields = ['id', 'parameter', 'value']
        read_only_fields = ['id']


class ProductInfoSerializer(ModelSerializer):
    product = ProductSerializer(read_only=True)
    parameters = ProductParameterSerializer(read_only=True, many=True)

    class Meta:
        model = ProductInfo
        fields = ['id', 'external_id', 'product', 'model', 'shop', 'quantity',
                  'price', 'price_rrc', 'parameters']
        read_only_fields = ['id']


class ContactSerializer(ModelSerializer):
    class Meta:
        model = Contact
        fields = ['city', 'street', 'house', 'building', 'structure',
                  'apartment', 'phone']


class OrderSerializer(ModelSerializer):
    total_sum = serializers.IntegerField()
    contact = ContactSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'dt', 'state', 'total_sum', 'contact']
        read_only_fields = ['id']
        extra_kwargs = {
            'user': {'write_only': True}
        }


class OrderItemSerializer(ModelSerializer):
    product_info = ProductInfoSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['order', 'product_info', 'quantity']


class OrderInfoSerializer(ModelSerializer):
    total_sum = serializers.IntegerField()
    contact = ContactSerializer(read_only=True)
    order_items = OrderItemSerializer(read_only=True, many=True)
    user = UserSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ['dt', 'state', 'user', 'contact', 'order_items', 'total_sum']
