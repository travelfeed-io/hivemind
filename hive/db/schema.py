"""Db schema definitions and setup routines."""

import sqlalchemy as sa
from sqlalchemy.sql import text as sql_text
from sqlalchemy.types import SMALLINT
from sqlalchemy.types import CHAR
from sqlalchemy.types import VARCHAR
from sqlalchemy.types import TEXT
from sqlalchemy.types import BOOLEAN
from sqlalchemy.types import BIGINT
from geoalchemy2.types import Geography

#pylint: disable=line-too-long, too-many-lines

DB_VERSION = 12

def build_metadata():
    """Build schema def with SqlAlchemy"""
    metadata = sa.MetaData()

    sa.Table(
        'hive_blocks', metadata,
        sa.Column('num', sa.Integer, primary_key=True, autoincrement=False),
        sa.Column('hash', CHAR(40), nullable=False),
        sa.Column('prev', CHAR(40)),
        sa.Column('txs', SMALLINT, server_default='0', nullable=False),
        sa.Column('ops', SMALLINT, server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),

        sa.UniqueConstraint('hash', name='hive_blocks_ux1'),
        sa.ForeignKeyConstraint(['prev'], ['hive_blocks.hash'], name='hive_blocks_fk1'),
        mysql_engine='InnoDB',
        mysql_default_charset='utf8mb4'
    )

    sa.Table(
        'hive_accounts', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', VARCHAR(16), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        #sa.Column('block_num', sa.Integer, nullable=False),
        sa.Column('reputation', sa.Float(precision=6), nullable=False, server_default='25'),

        sa.Column('display_name', sa.String(20)),
        sa.Column('about', sa.String(160)),
        sa.Column('location', sa.String(30)),
        sa.Column('website', sa.String(100)),
        sa.Column('facebook', sa.String(50)),
        sa.Column('twitter', sa.String(15)),
        sa.Column('instagram', sa.String(30)),
        sa.Column('youtube', sa.String(50)),
        sa.Column('couchsurfing', sa.String(50)),
        sa.Column('profile_image', sa.String(1024), nullable=False, server_default=''),
        sa.Column('cover_image', sa.String(1024), nullable=False, server_default=''),

        sa.Column('followers', sa.Integer, nullable=False, server_default='0'),
        sa.Column('following', sa.Integer, nullable=False, server_default='0'),

        sa.Column('proxy', VARCHAR(16), nullable=False, server_default=''),
        sa.Column('post_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('proxy_weight', sa.Float(precision=6), nullable=False, server_default='0'),
        sa.Column('vote_weight', sa.Float(precision=6), nullable=False, server_default='0'),
        sa.Column('kb_used', sa.Integer, nullable=False, server_default='0'), # deprecated
        sa.Column('rank', sa.Integer, nullable=False, server_default='0'),

        sa.Column('active_at', sa.DateTime, nullable=False, server_default='1970-01-01 00:00:00'),
        sa.Column('cached_at', sa.DateTime, nullable=False, server_default='1970-01-01 00:00:00'),
        sa.Column('raw_json', sa.Text),

        sa.UniqueConstraint('name', name='hive_accounts_ux1'),
        sa.Index('hive_accounts_ix1', 'vote_weight', 'id'), # core: quick ranks
        sa.Index('hive_accounts_ix2', 'name', 'id'), # core: quick id map
        sa.Index('hive_accounts_ix3', 'vote_weight', 'name', postgresql_ops=dict(name='varchar_pattern_ops')), # API: lookup
        sa.Index('hive_accounts_ix4', 'id', 'name'), # API: quick filter/sort
        sa.Index('hive_accounts_ix5', 'cached_at', 'name'), # core/listen sweep
        mysql_engine='InnoDB',
        mysql_default_charset='utf8mb4'
    )

    sa.Table(
        'hive_posts', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('parent_id', sa.Integer),
        sa.Column('author', VARCHAR(16), nullable=False),
        sa.Column('permlink', VARCHAR(255), nullable=False),
        sa.Column('community', VARCHAR(16), nullable=False),
        sa.Column('category', VARCHAR(255), nullable=False, server_default=''),
        sa.Column('depth', SMALLINT, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('is_deleted', BOOLEAN, nullable=False, server_default='0'),
        sa.Column('is_pinned', BOOLEAN, nullable=False, server_default='0'),
        sa.Column('is_muted', BOOLEAN, nullable=False, server_default='0'),
        sa.Column('is_valid', BOOLEAN, nullable=False, server_default='1'),
        sa.Column('promoted', sa.types.DECIMAL(10, 3), nullable=False, server_default='0'),

        sa.ForeignKeyConstraint(['author'], ['hive_accounts.name'], name='hive_posts_fk1'),
        sa.ForeignKeyConstraint(['community'], ['hive_accounts.name'], name='hive_posts_fk2'),
        sa.ForeignKeyConstraint(['parent_id'], ['hive_posts.id'], name='hive_posts_fk3'),
        sa.UniqueConstraint('author', 'permlink', name='hive_posts_ux1'),
        sa.Index('hive_posts_ix3', 'author', 'depth', 'id', postgresql_where=sql_text("is_deleted = '0'")), # API: author blog/comments
        sa.Index('hive_posts_ix4', 'parent_id', 'id', postgresql_where=sql_text("is_deleted = '0'")), # API: fetching children
        mysql_engine='InnoDB',
        mysql_default_charset='utf8mb4'
    )

    #sa.Table(
    #    'hive_tags', metadata,
    #    sa.Column('id', sa.Integer, primary_key=True),
    #    sa.Column('name', CHAR(64), nullable=False),
    #    sa.UniqueConstraint('name', name='hive_tags_ux1'),
    #    mysql_engine='InnoDB',
    #    mysql_default_charset='utf8mb4'
    #)

    sa.Table(
        'hive_post_tags', metadata,
        sa.Column('post_id', sa.Integer, nullable=False),
        sa.Column('tag', sa.String(32), nullable=False),
        sa.UniqueConstraint('tag', 'post_id', name='hive_post_tags_ux1'), # core
        sa.Index('hive_post_tags_ix1', 'post_id'), # core
        mysql_engine='InnoDB',
        mysql_default_charset='utf8mb4'
    )

    sa.Table(
        'hive_follows', metadata,
        sa.Column('follower', sa.Integer, nullable=False),
        sa.Column('following', sa.Integer, nullable=False),
        sa.Column('state', SMALLINT, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime, nullable=False),

        sa.UniqueConstraint('following', 'follower', name='hive_follows_ux3'), # core
        sa.Index('hive_follows_ix5a', 'following', 'state', 'created_at', 'follower'),
        sa.Index('hive_follows_ix5b', 'follower', 'state', 'created_at', 'following'),
        mysql_engine='InnoDB',
        mysql_default_charset='utf8mb4'
    )

    sa.Table(
        'hive_reblogs', metadata,
        sa.Column('account', VARCHAR(16), nullable=False),
        sa.Column('post_id', sa.Integer, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),

        sa.ForeignKeyConstraint(['account'], ['hive_accounts.name'], name='hive_reblogs_fk1'),
        sa.ForeignKeyConstraint(['post_id'], ['hive_posts.id'], name='hive_reblogs_fk2'),
        sa.UniqueConstraint('account', 'post_id', name='hive_reblogs_ux1'), # core
        sa.Index('hive_reblogs_ix1', 'post_id', 'account', 'created_at'), # API -- TODO: seemingly unused
        mysql_engine='InnoDB',
        mysql_default_charset='utf8mb4'
    )

    sa.Table(
        'hive_payments', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('block_num', sa.Integer, nullable=False),
        sa.Column('tx_idx', SMALLINT, nullable=False),
        sa.Column('post_id', sa.Integer, nullable=False),
        sa.Column('from_account', sa.Integer, nullable=False),
        sa.Column('to_account', sa.Integer, nullable=False),
        sa.Column('amount', sa.types.DECIMAL(10, 3), nullable=False),
        sa.Column('token', VARCHAR(5), nullable=False),

        sa.ForeignKeyConstraint(['from_account'], ['hive_accounts.id'], name='hive_payments_fk1'),
        sa.ForeignKeyConstraint(['to_account'], ['hive_accounts.id'], name='hive_payments_fk2'),
        sa.ForeignKeyConstraint(['post_id'], ['hive_posts.id'], name='hive_payments_fk3'),
        mysql_engine='InnoDB',
        mysql_default_charset='utf8mb4'
    )

    sa.Table(
        'hive_communities', metadata,
        sa.Column('name', VARCHAR(16), primary_key=True),
        sa.Column('title', sa.String(32), nullable=False),
        sa.Column('about', sa.String(255), nullable=False, server_default=''),
        sa.Column('description', sa.String(5000), nullable=False, server_default=''),
        sa.Column('lang', CHAR(2), nullable=False, server_default='en'),
        sa.Column('settings', TEXT, nullable=False),
        sa.Column('type_id', SMALLINT, nullable=False, server_default='0'),
        sa.Column('is_nsfw', BOOLEAN, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.ForeignKeyConstraint(['name'], ['hive_accounts.name'], name='hive_communities_fk1'),
        mysql_engine='InnoDB',
        mysql_default_charset='utf8mb4'
    )

    sa.Table(
        'hive_members', metadata,
        sa.Column('community', VARCHAR(16), nullable=False),
        sa.Column('account', VARCHAR(16), nullable=False),
        sa.Column('is_admin', BOOLEAN, nullable=False),
        sa.Column('is_mod', BOOLEAN, nullable=False),
        sa.Column('is_approved', BOOLEAN, nullable=False),
        sa.Column('is_muted', BOOLEAN, nullable=False),
        sa.Column('title', sa.String(255), nullable=False, server_default=''),
        sa.ForeignKeyConstraint(['community'], ['hive_communities.name'], name='hive_members_fk1'),
        sa.ForeignKeyConstraint(['account'], ['hive_accounts.name'], name='hive_members_fk2'),
        sa.UniqueConstraint('community', 'account', name='hive_members_ux1'),
        mysql_engine='InnoDB',
        mysql_default_charset='utf8mb4'
    )

    sa.Table(
        'hive_flags', metadata,
        sa.Column('account', VARCHAR(16), nullable=False),
        sa.Column('post_id', sa.Integer, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('notes', sa.String(255), nullable=False),
        sa.ForeignKeyConstraint(['account'], ['hive_accounts.name'], name='hive_flags_fk1'),
        sa.ForeignKeyConstraint(['post_id'], ['hive_posts.id'], name='hive_flags_fk2'),
        sa.UniqueConstraint('account', 'post_id', name='hive_flags_ux1'),
        mysql_engine='InnoDB',
        mysql_default_charset='utf8mb4'
    )

    sa.Table(
        'hive_modlog', metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('community', VARCHAR(16), nullable=False),
        sa.Column('account', VARCHAR(16), nullable=False),
        sa.Column('action', sa.String(32), nullable=False),
        sa.Column('params', sa.String(1000), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.ForeignKeyConstraint(['community'], ['hive_communities.name'], name='hive_modlog_fk1'),
        sa.ForeignKeyConstraint(['account'], ['hive_accounts.name'], name='hive_modlog_fk2'),
        sa.Index('hive_modlog_ix1', 'community', 'created_at'),
        mysql_engine='InnoDB',
        mysql_default_charset='utf8mb4'
    )

    sa.Table(
        'hive_feed_cache', metadata,
        sa.Column('post_id', sa.Integer, nullable=False),
        sa.Column('account_id', sa.Integer, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.UniqueConstraint('post_id', 'account_id', name='hive_feed_cache_ux1'), # core
        sa.Index('hive_feed_cache_ix1', 'account_id', 'post_id', 'created_at'), # API (and rebuild?)
        mysql_engine='InnoDB',
        mysql_default_charset='utf8mb4'
    )

    sa.Table(
        'hive_posts_cache', metadata,
        sa.Column('post_id', sa.Integer, primary_key=True),
        sa.Column('author', VARCHAR(16), nullable=False),
        sa.Column('permlink', VARCHAR(255), nullable=False),
        sa.Column('category', VARCHAR(255), nullable=False, server_default=''),

        # TravelFeed Geo-Location enables filtering for posts by location and creating location categories
        sa.Column('latitude', sa.Float(precision=4)),
        sa.Column('longitude', sa.Float(precision=4)),
        # sa.Column('geo_location', Geography(geometry_type='POINT', srid=4326)), #PostGIS for better location queries. Important: Comment out this line on first start of `hive sync`, then open psql, connect to the db and execute `CREATE EXTENSION postgis;`, then restart `hive sync` with this line not commented out. Todo: Find way to create extension from sqlalchemy
        sa.Column('osm_type', VARCHAR(1)),
        sa.Column('osm_id', BIGINT),
        sa.Column('country_code', VARCHAR(2)), # The country names and the region/continent the countries are in can later be obtained through the API
        sa.Column('subdivision', VARCHAR(100)),
        sa.Column('city', VARCHAR(100)),
        sa.Column('suburb', VARCHAR(100)),

         # Enables querying for valid TravelFeed posts only
        sa.Column('is_travelfeed', BOOLEAN, nullable=False, server_default='0'),

         # TravelFeed Curation score
        sa.Column('curation_score', sa.Integer, nullable=False, server_default='0'),

        # important/index
        sa.Column('depth', SMALLINT, nullable=False, server_default='0'),
        sa.Column('children', SMALLINT, nullable=False, server_default='0'),

        # basic/extended-stats
        sa.Column('author_rep', sa.Float(precision=6), nullable=False, server_default='0'),
        sa.Column('flag_weight', sa.Float(precision=6), nullable=False, server_default='0'),
        sa.Column('total_votes', sa.Integer, nullable=False, server_default='0'),
        sa.Column('up_votes', sa.Integer, nullable=False, server_default='0'),

        # basic ui fields
        sa.Column('title', sa.String(255), nullable=False, server_default=''),
        sa.Column('preview', sa.String(1024), nullable=False, server_default=''),
        sa.Column('img_url', sa.String(1024), nullable=False, server_default=''),

        # core stats/indexes
        sa.Column('payout', sa.types.DECIMAL(10, 3), nullable=False, server_default='0'),
        sa.Column('promoted', sa.types.DECIMAL(10, 3), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default='1990-01-01'),
        sa.Column('payout_at', sa.DateTime, nullable=False, server_default='1990-01-01'),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default='1990-01-01'),
        sa.Column('is_paidout', BOOLEAN, nullable=False, server_default='0'),

        # ui flags/filters
        sa.Column('is_nsfw', BOOLEAN, nullable=False, server_default='0'),
        sa.Column('is_declined', BOOLEAN, nullable=False, server_default='0'),
        sa.Column('is_full_power', BOOLEAN, nullable=False, server_default='0'),
        sa.Column('is_hidden', BOOLEAN, nullable=False, server_default='0'),
        sa.Column('is_grayed', BOOLEAN, nullable=False, server_default='0'),

        # important indexes
        sa.Column('rshares', sa.BigInteger, nullable=False, server_default='0'),
        sa.Column('sc_trend', sa.Float(precision=6), nullable=False, server_default='0'),
        sa.Column('sc_hot', sa.Float(precision=6), nullable=False, server_default='0'),

        # bulk data
        sa.Column('body', TEXT),
        sa.Column('votes', TEXT),
        sa.Column('json', sa.Text),
        sa.Column('raw_json', sa.Text),

        sa.Index('hive_posts_cache_ix2', 'promoted', postgresql_where=sql_text("is_paidout = '0' AND promoted > 0")), # API
        sa.Index('hive_posts_cache_ix3', 'payout_at', 'post_id', postgresql_where=sql_text("is_paidout = '0'")), # core
        sa.Index('hive_posts_cache_ix6a', 'sc_trend', 'post_id', postgresql_where=sql_text("is_paidout = '0'")), # API: global trending
        sa.Index('hive_posts_cache_ix7a', 'sc_hot', 'post_id', postgresql_where=sql_text("is_paidout = '0'")), # API: global hot
        sa.Index('hive_posts_cache_ix6b', 'post_id', 'sc_trend', postgresql_where=sql_text("is_paidout = '0'")), # API: filtered trending
        sa.Index('hive_posts_cache_ix7b', 'post_id', 'sc_hot', postgresql_where=sql_text("is_paidout = '0'")), # API: filtered hot
        sa.Index('hive_posts_cache_ix8', 'category', 'payout', 'depth', postgresql_where=sql_text("is_paidout = '0'")), # API: tag stats
        sa.Index('hive_posts_cache_ix9a', 'depth', 'payout', 'post_id', postgresql_where=sql_text("is_paidout = '0'")), # API: payout
        sa.Index('hive_posts_cache_ix9b', 'category', 'depth', 'payout', 'post_id', postgresql_where=sql_text("is_paidout = '0'")), # API: filtered payout

        mysql_engine='InnoDB',
        mysql_default_charset='utf8mb4'
    )

    sa.Table(
        'hive_state', metadata,
        sa.Column('block_num', sa.Integer, primary_key=True, autoincrement=False),
        sa.Column('db_version', sa.Integer, nullable=False),
        sa.Column('steem_per_mvest', sa.types.DECIMAL(8, 3), nullable=False),
        sa.Column('usd_per_steem', sa.types.DECIMAL(8, 3), nullable=False),
        sa.Column('sbd_per_steem', sa.types.DECIMAL(8, 3), nullable=False),
        sa.Column('dgpo', sa.Text, nullable=False),

        mysql_engine='InnoDB',
        mysql_default_charset='utf8mb4'
    )

    return metadata

def teardown(db):
    """Drop all tables"""
    build_metadata().drop_all(db.engine())

def setup(db):
    """Creates all tables and seed data"""
    # initialize schema
    build_metadata().create_all(db.engine())

    # tune auto vacuum/analyze
    reset_autovac(db)

    # default rows
    sqls = [
        "INSERT INTO hive_state (block_num, db_version, steem_per_mvest, usd_per_steem, sbd_per_steem, dgpo) VALUES (0, %d, 0, 0, 0, '')" % DB_VERSION,
        "INSERT INTO hive_blocks (num, hash, created_at) VALUES (0, '0000000000000000000000000000000000000000', '2016-03-24 16:04:57')",
        "INSERT INTO hive_accounts (name, created_at) VALUES ('miners',    '2016-03-24 16:05:00')",
        "INSERT INTO hive_accounts (name, created_at) VALUES ('null',      '2016-03-24 16:05:00')",
        "INSERT INTO hive_accounts (name, created_at) VALUES ('temp',      '2016-03-24 16:05:00')",
        "INSERT INTO hive_accounts (name, created_at) VALUES ('initminer', '2016-03-24 16:05:00')"]
    for sql in sqls:
        db.query(sql)

def reset_autovac(db):
    """Initializes/resets per-table autovacuum/autoanalyze params.

    We use a scale factor of 0 and specify exact threshold tuple counts,
    per-table, in the format (autovacuum_threshold, autoanalyze_threshold)."""

    autovac_config = { #    vacuum  analyze
        'hive_accounts':    (50000, 100000),
        'hive_posts_cache': (25000, 25000),
        'hive_posts':       (2500, 10000),
        'hive_post_tags':   (5000, 10000),
        'hive_follows':     (5000, 5000),
        'hive_feed_cache':  (5000, 5000),
        'hive_blocks':      (5000, 25000),
        'hive_reblogs':     (5000, 5000),
        'hive_payments':    (5000, 5000),
    }

    for table, (n_vacuum, n_analyze) in autovac_config.items():
        sql = """ALTER TABLE %s SET (autovacuum_vacuum_scale_factor = 0,
                                     autovacuum_vacuum_threshold = %s,
                                     autovacuum_analyze_scale_factor = 0,
                                     autovacuum_analyze_threshold = %s)"""
        db.query(sql % (table, n_vacuum, n_analyze))
