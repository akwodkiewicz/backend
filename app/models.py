import graphene
from sys import stderr

from . import app, mongo
from .views import list_users_page


class WatchedPage(graphene.ObjectType):
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
    _id = graphene.ID()
    username = graphene.String()
    password = graphene.String()
    email = graphene.String()
    watched_pages = graphene.List(lambda: WatchedPage)

    def resolve_watched_pages(self, args, context, info):
        result = list(mongo.db.watched_pages.find({"owner_name":self.username}))
        if result is not None:
            return [WatchedPage(**kwargs) for kwargs in result]
        return None


class Query(graphene.ObjectType):
    users = graphene.List(User,
                        _id=graphene.ID(),
                        username=graphene.String()
                        )
    watched_pages = graphene.List(WatchedPage,
                        _id=graphene.ID(),
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
            query_dict['_id'] = _id
        if args.get('owner_name') is not None:
            query_dict['owner_name'] = owner_name
        if args.get('page_name') is not None:
            query_dict['page_name'] = page_name
        if args.get('url') is not None:
            query_dict['url'] = url
        result = list(mongo.db.watched_pages.find(query_dict))
        if result is not None:
            return [WatchedPage(**kwargs) for kwargs in result]
        return None


schema = graphene.Schema(query=Query, auto_camelcase=False)
