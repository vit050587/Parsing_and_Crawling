import scrapy
import json
from scrapy.http import HtmlResponse
from instaparser.items import InstaparserItem
import re
from urllib.parse import urlencode
from copy import deepcopy

class InstagramSpider(scrapy.Spider):
    name = 'instagram'
    allowed_domains = ['instagram.com']
    start_urls = ['https://www.instagram.com/']
    inst_login_link = 'https://www.instagram.com/accounts/login/ajax/'
    inst_login = 'Onliskill_udm'
    inst_pwd = '#PWD_INSTAGRAM_BROWSER:10:1650388687:AUVQAPLsNiCtdG0b660bL/la/fAfzNJ0AaVNGPhAI7fwS9ANR85sT7Kjag60UVTeviSs34AXFch4cAYMc8Pq56W6i7ntwpu2ucSOa3aIY3LRVrPRqB2XvkxeB+KW6C2TQEPNVbnxpAqk8m4yOJg='
    parse_users = ['_bikeland.kashirka_', 'bikeprogress']
    inst_graphql_link = 'https://www.instagram.com/graphql/query/?'
    followers_hash = 'c76146de99bb02f6415203be841dd25a'
    following_hash = 'd04b0a864b4b54837c0d870b0e77e076'


    def parse(self, response: HtmlResponse):
        csrf = self.fetch_csrf_token(response.text)
        yield scrapy.FormRequest(
            self.inst_login_link,
            method='POST',
            callback=self.login,
            formdata={'username': self.inst_login, 'enc_password': self.inst_pwd},
            headers={'X-CSRFToken': csrf}
        )

    def login(self, response: HtmlResponse):
        j_body = response.json()
        if j_body.get('authenticated'):
            for username in self.parse_users:
                yield response.follow(
                    f'/{username}',
                    callback=self.user_data_parse,
                    cb_kwargs={'username': username}
                )

    def user_data_parse(self, response: HtmlResponse, username):
        user_id = self.fetch_user_id(response.text, username)
        variables = {'id': user_id,
                     'include_reel': True,
                     'fetch_mutual': True,
                     'first': 24}

        yield response.follow(f'{self.inst_graphql_link}query_hash={self.followers_hash}&{urlencode(variables)}',
                              callback=self.followers_parse,
                              cb_kwargs={'username': username,
                                         'user_id': user_id,
                                         'variables': deepcopy(variables)},
                              headers={'User-Agent': 'Instagram 155.0.0.37.107'})

        yield response.follow(f'{self.inst_graphql_link}query_hash={self.following_hash}&{urlencode(variables)}',
                              callback=self.followers_parse,
                              cb_kwargs={'username': username,
                                         'user_id': user_id,
                                         'variables': deepcopy(variables)},
                              headers={'User-Agent': 'Instagram 155.0.0.37.107'})

    def followers_parse(self, response: HtmlResponse, username, user_id, variables):
        followers_json = json.loads(response.text)
        page_info = followers_json.get('data').get('user').get('edge_followed_by').get('page_info')
        if page_info.get('has_next_page'):
            variables['after'] = page_info['end_cursor']
            followers_url = f'{self.inst_graphql_link}query_hash={self.followers_hash}&{urlencode(variables)}'
            yield response.follow(
                followers_url,
                callback=self.followers_parse,
                cb_kwargs={
                    'username': username,
                    'user_id': user_id,
                    'variables': deepcopy(variables)})
        followers = followers_json.get('data').get('user').get('edge_followed_by').get('edges')
        for follower in followers:
            profile = {
                '_id': username + '_' + follower['node']['id'],
                'collection': 'followers',
                'id': follower['node']['id'],
                'username': follower['node']['username'],
                'full_name': follower['node']['full_name'],
                'profile_pic_url': follower['node']['profile_pic_url'],
                'main_user_name_id': username + '/' + user_id}
            yield InstaparserItem(**profile)

    def followings_parse(self, response: HtmlResponse, username, user_id, variables):
        followings_json = json.loads(response.text)
        page_info = followings_json.get('data').get('user').get('edge_follow').get('page_info')
        if page_info.get('has_next_page'):
            variables['after'] = page_info['end_cursor']
            followings_url = f'{self.inst_graphql_link}query_hash={self.following_hash}&{urlencode(variables)}'

            yield response.follow(
                followings_url,
                callback=self.followings_parse,
                cb_kwargs={
                    'username': username,
                    'user_id': user_id,
                    'variables': deepcopy(variables)})

        followings = followings_json.get('data').get('user').get('edge_follow').get('edges')
        for following in followings:
            profile = {
                '_id': username + '_' + following['node']['id'],
                'collection': 'followings',
                'id': following['node']['id'],
                'username': following['node']['username'],
                'full_name': following['node']['full_name'],
                'profile_pic_url': following['node']['profile_pic_url'],
                'main_user_name_id': username + '/' + user_id}
            yield InstaparserItem(**profile)


    def fetch_csrf_token(self, text):
        matched = re.search('\"csrf_token\":\"\\w+\"', text).group()
        return matched.split(':').pop().replace(r'"', '')

    def fetch_user_id(self, text, username):
        try:
            matched = re.search(
                '{\"id\":\"\\d+\",\"username\":\"%s\"}' % username, text
            ).group()
            return json.loads(matched).get('id')
        except:
            return re.findall('\"id\":\"\\d+\"', text)[-1].split('"')[-2]