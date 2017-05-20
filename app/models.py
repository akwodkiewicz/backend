import graphene
from sys import stderr
from graphene import relay
from . import app, mongo
from .views import list_users_page
from .logic import add_to_watched_pages, delete_from_watched_pages, add_to_users, login, self_info


class WatchedPage(graphene.ObjectType):
    class Meta:
        interfaces = (relay.Node,)

    _id = graphene.ID()
    owner_name = graphene.String()
    page_name = graphene.String()
    url = graphene.String()
    authentication = graphene.String()
    interval = graphene.Int()
    user = graphene.Field(lambda: User)

    def resolve_user(self, args, context, info):
        query_dict = {}
        if self.owner_name is not None:
            query_dict['username'] = self.owner_name
        result = mongo.db.users.find_one(query_dict)
        if result is not None:
            return User(**result)
        return None


class User(graphene.ObjectType):
    class Meta:
        interfaces = (relay.Node,)

    _id = graphene.ID()
    username = graphene.String()
    password = graphene.String()
    email = graphene.String()
    watched_pages = graphene.List(lambda: WatchedPage)

    def resolve_watched_pages(self, args, context, info):
        result = list(mongo.db.watched_pages.find({"owner_name": self.username}))
        if result is not None:
            return [WatchedPage(**kwargs) for kwargs in result]
        return None


class NewWatchedPage(graphene.Mutation):
    class Input:
        url = graphene.String(required=True)
        page_name = graphene.String(required=True)
        owner_name = graphene.String(required=True)
        authentication = graphene.String(required=False)
        interval = graphene.String(required=False)

    success = graphene.Boolean()

    @staticmethod
    def mutate(root, input, context, info):
        url = input.get('url')
        page_name = input.get('page_name')
        owner_name = input.get('owner_name')
        result = add_to_watched_pages(owner_name, page_name, url)
        return NewWatchedPage(success=result)


class DeleteWatchedPage(graphene.Mutation):
    class Input:
        page_name = graphene.String(required=True)
        owner_name = graphene.String(required=True)

    success = graphene.Boolean()

    @staticmethod
    def mutate(root, input, context, info):
        page_name = input.get('page_name')
        owner_name = input.get('owner_name')
        result = delete_from_watched_pages(owner_name, page_name)
        return DeleteWatchedPage(success=result)


class NewUser(graphene.Mutation):
    class Input:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        email = graphene.String(required=True)

    success = graphene.Boolean()

    @staticmethod
    def mutate(root, input, context, info):
        username = input.get('username')
        password = input.get('password')
        email = input.get('email')
        result = add_to_users(username, password, email)
        return NewUser(success=result)


class UserLogin(graphene.Mutation):
    class Input:
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    token = graphene.String()

    @staticmethod
    def mutate(root, input, context, info):
        username = input.get('username')
        password = input.get('password')
        result = login(username, password)
        return UserLogin(token=result)


class SelfInfo(graphene.Mutation):
    class Input:
        token = graphene.String()

    User = graphene.Field(User)

    @staticmethod
    def mutate(root, input, context, info):
        token = input.get('token')
        result = self_info(token)
        return SelfInfo(User=result)


class Mutation(graphene.ObjectType):
    NewWatchedPage = NewWatchedPage.Field()
    DeleteWatchedPage = DeleteWatchedPage.Field()
    NewUser = NewUser.Field()
    UserLogin = UserLogin.Field()
    SelfInfo = SelfInfo.Field()


class Query(graphene.ObjectType):
    users = graphene.List(User,
                          _id=graphene.ID(),
                          username=graphene.String()
                          )
    watched_pages = graphene.List(WatchedPage,
                                  _id=graphene.ID(),
                                  owner_name=graphene.String(),
                                  page_name=graphene.String(),
                                  url=graphene.String()
                                  )

    @staticmethod
    def resolve_users(self, args, context, info):
        query_dict = {}
        if args.get('username') is not None:
            query_dict['username'] = args['username']
        result = list(mongo.db.users.find(query_dict))
        if result is not None:
            return [User(**kwargs) for kwargs in result]
        return None

    @staticmethod
    def resolve_watched_pages(self, args, context, info):
        query_dict = {}
        if args.get('_id') is not None:
            query_dict['_id'] = args.get('_id')
        if args.get('owner_name') is not None:
            query_dict['owner_name'] = args.get('owner_name')
        if args.get('page_name') is not None:
            query_dict['page_name'] = args.get('page_name')
        if args.get('url') is not None:
            query_dict['url'] = args.get('url')
        result = list(mongo.db.watched_pages.find(query_dict))
        if result is not None:
            return [WatchedPage(**kwargs) for kwargs in result]
        return None


schema = graphene.Schema(query=Query, auto_camelcase=False, mutation=Mutation)
