import json

from django.http import HttpResponse, Http404
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Customers, Account, Wallet
from .serializers import CustomersSerializer, AccountSerializer, WalletSerializer


class CustomerList(APIView):
    def get(self, request):
        customers1 = Customers.objects.all() #obtener todas las instancias de customers
        serializer = CustomersSerializer(customers1, many=True)
        return Response(serializer.data)

    def post(self, request):
        if request.method == 'POST':
            received_json_data = json.loads(request.body)

            new_customer_user = User.objects.create_user(username=received_json_data['user'],
                                                    email=received_json_data['email'],
                                                    first_name=received_json_data['first_name'],
                                                    last_name=received_json_data['last_name'],
                                                    password=received_json_data['password'])
            new_customer_user.save()
            new_customer = Customers(first_name=received_json_data['first_name'],
                                     last_name=received_json_data['last_name'],
                                     address=received_json_data['address'],
                                     phone=received_json_data['phone'],
                                     customer_id=new_customer_user.id)
            new_customer.save()
        return HttpResponse(status=201)
    
    
class AccountList(APIView):
    def get(self, request):
        accounts = Account.objects.all() #obtener todas las instancias de Accounts
        serializer = AccountSerializer(accounts, many=True)
        return Response(serializer.data)

    def post(self, request):
        if request.method == 'POST':
            received_json_data = json.loads(request.body)
            print(received_json_data['customer_id'])
            print(received_json_data['account_number'])
            print(received_json_data['balance']) 
            new_account = Account(customer_id=received_json_data['customer_id'], # read customer_id from the token in the future
                                  account_number=received_json_data['account_number'],
                                  balance=received_json_data['balance'])
            new_account.save()
        return HttpResponse(status=201)
    

class WalletsList(APIView):
    def get(self, request):
        wallet = Wallet.objects.all() #obtener todas las instancias de Wallets
        serializer = WalletSerializer(wallet, many=True)
        return Response(serializer.data)

    def post(self, request):
        if request.method == 'POST':
            received_json_data = json.loads(request.body)
            account = Account.objects.filter(account_number = received_json_data['account_number'])
            if not account.exists():
                raise Http404 ("The requested Wallet was not found.")
            else:
                new_wallet = Wallet(wallet_number=received_json_data['wallet_number'], 
                                    account_number=received_json_data['account_number'],
                                    balance=received_json_data['balance'],
                                    beneficiary_id=['beneficiary_id'])
            new_wallet.save()
        return HttpResponse(status=201)
    

class CustomerOnly(APIView):
    def get(self, request, customer_id):
        try:
            customer = Customers.objects.get(customer_id=customer_id)
            serializer = CustomersSerializer(instance=customer)
            return Response(serializer.data)
        except Customers.DoesNotExist:
            raise Http404 ("The requested Customer was not found.")

    def delete(self, request, customer_id):
        try:        
            accounts = Account.objects.filter(customer_id=customer_id)
            customer = Customers.objects.filter(customer_id=customer_id)
            user = User.objects.filter(id=customer_id)

            if not accounts.exists() and not customer.exists() and not user.exists():
                raise Http404 ("The requested Customer was not found.")

            for account in accounts:
                account.delete()                       
            customer.delete()
            user.delete()
            return HttpResponse(status=200)
        except Account.DoesNotExist:
            raise Http404 ("The requested Customer was not found.")
        

class AccountOnly(APIView):
    def get(self, request, customer_id):
        try:
            account = Account.objects.filter(customer_id=customer_id)
            if not account.exists():
                raise Http404 ("The requested Account was not found.")
            
            serializer = AccountSerializer(instance=account, many=True)
            return Response(serializer.data)
        except Account.DoesNotExist:
            raise Http404 ("The requested Account was not found.")
        
    def delete(self, request, customer_id, account_number):
        try:
            account = Account.objects.filter(customer_id=customer_id, account_number=account_number)
            if not account.exists():
                raise Http404 ("The requested Account was not found.")

            account.delete()
            return HttpResponse(status=200)
        except Account.DoesNotExist:
            raise Http404 ("The requested Account was not found.")


class WalletOnly(APIView):
    def get(self, request, account_number):
        try:
            wallet = Wallet.objects.filter(account_number)
            if not wallet.exists():
                raise Http404 ("The requested Wallet was not found.")
            serializer=WalletSerializer(instance=wallet, many=True)
            return Response(serializer.data)
        except Wallet.DoesNotExist:
            raise Http404 ("The requested Account was not found.")

    def delete(self, request, account_number):
        try:
            wallet = Wallet.objects.filter(account_number=account_number)
            if not wallet.exists():
                raise Http404 ("The requested Wallet was not found.")
            wallet.delete()
            return HttpResponse(status=200)
        except Account.DoesNotExist:
            raise Http404 ("The requested Wallet was not found.")  
        



class DepositInAccountOnly(APIView):
    def post(self, request, customer_id):
        try:
            received_json_data = json.loads(request.body)
            account_number = received_json_data['account_number']
            deposit_to_do = float(received_json_data['deposit'])
            deposit_limit = 10000
            if deposit_to_do > deposit_limit:
                return HttpResponse(status=400, reason="Deposit Limit is exceeded, deposits should be under 10,000")
            account = Account.objects.get(customer_id=customer_id, account_number=account_number)
            account.balance = str(float(account.balance) + deposit_to_do)
            account.save()
            serializer = AccountSerializer(instance=account, many=False)
            return Response(serializer.data)
        except Account.DoesNotExist:
            raise Http404 ("The requested Account was not found.")
        
    
class WithdrawInAccount(APIView):
    def is_transaction_valid(self, current_balance, withdraw_to_do):
        limit_porcentual_threshold = 90
        balance_limit = 100
        if current_balance >= withdraw_to_do:
            withdraw_to_do_porcentual = (withdraw_to_do * 100) / current_balance
            if withdraw_to_do_porcentual <= limit_porcentual_threshold and (current_balance - withdraw_to_do) >= balance_limit:
                return True
        return False 
    

    def post(self, request, customer_id):
        try:
            received_json_data = json.loads(request.body)
            account_number = received_json_data['account_number']
            withdraw_to_do = float(received_json_data['withdraw'])
            account = Account.objects.get(customer_id=customer_id, account_number=account_number)            
            current_balance = float(account.balance)            
            if self.is_transaction_valid(current_balance, withdraw_to_do):
                account = Account.objects.get(customer_id=customer_id, account_number=account_number)
                account.balance = str(current_balance - withdraw_to_do)
                account.save()
                serializer = AccountSerializer(instance=account, many=False)
                return Response(serializer.data)                
            else:
                return HttpResponse(status=400, reason="The account cannot have less than $100 in balance or exceed the withdrawal limit.")
        except Account.DoesNotExist:
            raise Http404 ("The requested Account was not found.")
          

class UserLogin(APIView):
    def post(self, request):
        if request.method == 'POST':
            received_json_data = json.loads(request.body)
            print(received_json_data['user'])
            print(received_json_data['password'])
        # example of Login
        user = authenticate(username=received_json_data['user'], password=received_json_data['password'])
        if user is not None:
            print('El usuario ha sido loggeado')
            print(user.first_name)
            print(user.email)
            print(user.is_staff)

            responseData = {
                'id': user.id,
                'name': user.first_name,
                'last_name': user.last_name,
                'is_staff': user.is_staff
            }
            if user.is_staff:
                return HttpResponse(json.dumps(responseData), content_type="application/json", status=202)

            return HttpResponse(json.dumps(responseData), content_type="application/json")
        else:
            print('User was NOT LOGGED IN')
            return HttpResponse(status=404)
