
```
docker compose down
docker volume rm stockurajp_postgres_data
docker compose up -d 
docker compose exec web alembic upgrade head 
docker compose down && docker compose up -d
```

```
docker compose exec db psql -U postgres -d stockura
select * from companies;
```