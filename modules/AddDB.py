import psycopg2


connection = psycopg2.connect(**db_config)

# def AddDB(OnionName, Title, url, RawText, Summary, DetailedText, Links, Images, ImageCaptions, ImageText, EXIFData, ScreenShots):
#     DateNow = datetime.now().date()
#     with connection.cursor() as cursor:
#         cursor.execute('INSERT INTO intelligence (link, date, title, url, rawtext, summary, detailedtext, links, images, imagecaptions, imagetext, exifdata, screenshots) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (OnionName, DateNow, Title, url, RawText, Summary, DetailedText, Links, Images, ImageCaptions, ImageText, EXIFData, ScreenShots))
#     connection.commit()
#     return "Done"

def AddDB(timestamp, link, title, rawtext, summary, detailedtext, categorytags, legalorillegal, links, images, imagecaptions, imagetext, exifdata, screenshots, emailid, cryptocoin, address, transactions, balance):   
    with connection.cursor() as cursor:
        try:
            sql_query = f"""INSERT INTO intelligence (
                    timestamp,
                    link,
                    title,
                    rawtext,
                    summary,
                    detailedtext,
                    categorytags,
                    legalorillegal,
                    links,
                    images,
                    imagecaptions,
                    imagetext,
                    exifdata,
                    screenshots,
                    emailid,
                    cryptocoin,
                    address,
                    transactions,
                    balance
                ) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            data = (timestamp, link, title, rawtext, summary, detailedtext, categorytags, legalorillegal, links, images, imagecaptions, imagetext, exifdata, screenshots, emailid, cryptocoin, address, transactions, balance)
            cursor.execute(sql_query, data)
            connection.commit()
        except (Exception, psycopg2.Error) as error:
            print("Error adding data to PostgreSQL:", error)
            return False
        finally:
            if connection:
                cursor.close()
                connection.close()
            return True
