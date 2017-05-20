import graphene
from sys import stderr
from graphene import relay
from . import app, mongo
from .views import list_users_page
from .logic import add_to_watched_pages, delete_from_watched_pages, add_to_users


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

    @classmethod
    def get_node(cls, id, context, info):
        result = list(mongo.db.watched_pages.find({"_id": id}))
        return [WatchedPahedPge(**kwargs) for kwargs in result]


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

    @classmethod
    def get_node(cls, id, context, info):
        result = list(mongo.db.users.find({"_id": id}))
        return [WatchedPage(**kwargs) for kwargs in result]


class NewWatchedPage(graphene.Mutation):
    class Input:
        url = graphene.String(required=True)
        page_name = graphene.String(required=True)
        owner_name = graphene.String(required=True)
        authentication = graphene.String(required=False)
        interval = graphene.String(required=False)

    WatchedPage = graphene.Field(WatchedPage)

    @staticmethod
    def mutate(root, input, context, info):
        url = input.get('url')
        page_name = input.get('page_name')
        owner_name = input.get('owner_name')
        new_page = add_to_watched_pages(owner_name, page_name, url)
        return NewWatchedPage(WatchedPage=new_page)


class DeleteWatchedPage(graphene.Mutation):
    class Input:
        page_name = graphene.String(required=True)
        owner_name = graphene.String(required=True)

    WatchedPage = graphene.Field(WatchedPage)

    @staticmethod
    def mutate(root, input, context, info):
        page_name = input.get('page_name')
        owner_name = input.get('owner_name')
        deleted_page = delete_from_watched_pages(owner_name, page_name)
        return DeleteWatchedPage(WatchedPage=deleted_page)


class NewUser(graphene.Mutation):
    class Input:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        email = graphene.String(required=True)

    User = graphene.Field(User)

    @staticmethod
    def mutate(root, input, context, info):
        username = input.get('username')
        password = input.get('password')
        email = input.get('email')
        new_user = add_to_users(username, password, email)
        return NewUser(User=new_user)


class Mutation(graphene.ObjectType):
    NewWatchedPage = NewWatchedPage.Field()
    DeleteWatchedPage = DeleteWatchedPage.Field()
    NewUser = NewUser.Field()


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

    def resolve_users(self, args, context, info):
        query_dict = {}
        if args.get('username') is not None:
            query_dict['username'] = args['username']
        result = list(mongo.db.users.find(query_dict))
        if result is not None:
            return [User(**kwargs) for kwargs in result]
        return None

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
