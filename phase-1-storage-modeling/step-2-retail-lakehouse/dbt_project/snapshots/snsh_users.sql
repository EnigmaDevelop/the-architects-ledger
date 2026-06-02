{% snapshot snsh_users %}

{{
    config(
      target_schema='main',
      unique_key='user_id',
      strategy='check',
      check_cols=['email', 'country'],
      updated_at='updated_at'
    )
}}

select 
    user_id,
    email,
    country,
    updated_at
from {{ source('raw_lake', 'users') }}

{% endsnapshot %}
