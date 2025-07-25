import asyncio
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from app.models import Cafe, Category, CafeCategory
from app.data.data import categories_data, cafes_data
from app.database import async_session, create_tables


async def seed_database():
    async with async_session() as session:
        try:
            # Проверяем категории
            result = await session.execute(select(Category))
            existing_categories = {c.name: c for c in result.scalars().all()}

            for cat_data in categories_data:
                if cat_data['name'] not in existing_categories:
                    category = Category(name=cat_data['name'])
                    session.add(category)
            await session.commit()

            # Получаем актуальный словарь категорий
            result = await session.execute(select(Category))
            categories = {c.name: c.id for c in result.scalars().all()}

            # Проверяем, что все категории из cafes_data есть в categories
            all_cafe_categories = set()
            for cafe in cafes_data:
                all_cafe_categories.add(cafe['best_for'])
                all_cafe_categories.update(cafe['also_good_for'])
            missing = all_cafe_categories - set(categories.keys())
            if missing:
                print(f"Warning: Missing categories in categories_data: {missing}")

            # Проверяем текущее количество ассоциаций
            result = await session.execute(select(func.count()).select_from(CafeCategory))
            current_assoc_count = result.scalar()
            print(f"Current category associations in database: {current_assoc_count}")

            new_cafe_count = 0
            updated_cafe_count = 0
            assoc_added_count = 0
            assoc_updated_count = 0
            assoc_removed_count = 0

            for cafe_data in cafes_data:
                # Валидация длины строк
                if len(cafe_data['title']) > 255:
                    print(f"Error: Title too long for {cafe_data['title']}")
                    continue
                if len(cafe_data['city']) > 100:
                    print(f"Error: City too long for {cafe_data['title']}")
                    continue
                if cafe_data['image_url'] and len(cafe_data['image_url']) > 500:
                    print(f"Error: image_url too long for {cafe_data['title']}")
                    continue

                # Проверяем валидность категорий
                if cafe_data['best_for'] not in categories:
                    print(f"Invalid best_for category {cafe_data['best_for']} for {cafe_data['title']}")
                    continue
                invalid_cats = [cat for cat in cafe_data['also_good_for'] if cat not in categories]
                if invalid_cats:
                    print(f"Invalid also_good_for categories {invalid_cats} for {cafe_data['title']}")
                    continue

                # Проверка на дубликат: best_for не должно быть в also_good_for
                if cafe_data['best_for'] in cafe_data['also_good_for']:
                    print(
                        f"Error: Category {cafe_data['best_for']} is duplicated in best_for and also_good_for for {cafe_data['title']}")
                    continue

                # Уникальный набор категорий для кафе
                unique_categories = {cafe_data['best_for']} | set(cafe_data['also_good_for'])
                desired_category_ids = {categories[cat_name] for cat_name in unique_categories}
                best_for_id = categories[cafe_data['best_for']]

                # Проверяем, существует ли кафе
                result = await session.execute(
                    select(Cafe).filter_by(title=cafe_data['title'], city=cafe_data['city'])
                )
                existing_cafe = result.scalars().first()

                if existing_cafe:
                    # Обновляем существующие поля
                    updated = False
                    if existing_cafe.description != cafe_data['description']:
                        existing_cafe.description = cafe_data['description']
                        updated = True
                    if existing_cafe.image_url != cafe_data['image_url']:
                        existing_cafe.image_url = cafe_data['image_url']
                        updated = True
                    if updated:
                        updated_cafe_count += 1

                    # Получаем текущие ассоциации для кафе
                    result = await session.execute(
                        select(CafeCategory).filter_by(cafe_id=existing_cafe.id)
                    )
                    existing_assocs = {assoc.category_id: assoc for assoc in result.scalars().all()}
                    current_assoc_ids = set(existing_assocs.keys())

                    # Определяем, что нужно добавить, обновить или удалить
                    for cat_id in desired_category_ids:
                        is_best = (cat_id == best_for_id)
                        if cat_id in existing_assocs:
                            # Обновляем существующую ассоциацию, если изменился is_best
                            assoc = existing_assocs[cat_id]
                            if assoc.is_best != is_best:
                                assoc.is_best = is_best
                                assoc_updated_count += 1
                        else:
                            # Добавляем новую ассоциацию
                            assoc = CafeCategory(
                                cafe_id=existing_cafe.id,
                                category_id=cat_id,
                                is_best=is_best,
                            )
                            session.add(assoc)
                            assoc_added_count += 1

                    # Удаляем ассоциации, которых больше нет в desired_category_ids
                    for cat_id in current_assoc_ids - desired_category_ids:
                        session.delete(existing_assocs[cat_id])
                        assoc_removed_count += 1
                else:
                    # Добавляем новое кафе
                    cafe = Cafe(
                        title=cafe_data['title'],
                        city=cafe_data['city'],
                        description=cafe_data['description'],
                        image_url=cafe_data['image_url'],
                    )
                    session.add(cafe)
                    await session.flush()  # Нужен для получения cafe.id
                    for cat_name in unique_categories:
                        assoc = CafeCategory(
                            cafe_id=cafe.id,
                            category_id=categories[cat_name],
                            is_best=(cat_name == cafe_data['best_for']),
                        )
                        session.add(assoc)
                        assoc_added_count += 1
                    new_cafe_count += 1

                print(
                    f"Processed {cafe_data['title']} in {cafe_data['city']}, categories: best_for={cafe_data['best_for']}, also_good_for={cafe_data['also_good_for']}")

            print(f"Total new cafes added: {new_cafe_count}")
            print(f"Total cafes updated: {updated_cafe_count}")
            print(f"Total category associations added: {assoc_added_count}")
            print(f"Total category associations updated: {assoc_updated_count}")
            print(f"Total category associations removed: {assoc_removed_count}")
            await session.flush()
            await session.commit()
            print('Database seeded successfully!')
        except IntegrityError as e:
            await session.rollback()
            print(f"Error: Database conflict occurred - {e}")


async def main():
    await create_tables()
    await seed_database()


if __name__ == "__main__":
    asyncio.run(main())
