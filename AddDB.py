import psycopg2



connection = psycopg2.connect(**db_config)

def AddDB(timestamp, link, title, rawtext, summary, detailedtext, categorytags, legalorillegal, links, images, imagecaptions, imagetext, exifdata, emailid, cryptocoin, address, transactions, balance, ismalicious, virustotallink):   
    with connection.cursor() as cursor:
        try:
            #     screenshots,
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
               
                    

                    emailid,
                    cryptocoin,
                    address,
                    transactions,
                    balance,
                    ismalicious,
                    virustotallink
                ) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            # data = (timestamp, link, title, rawtext, summary, detailedtext, categorytags, legalorillegal, links, images, imagecaptions, imagetext, exifdata, screenshots, emailid, cryptocoin, address, transactions, balance, ismalicious, virustotallink)
            data = (timestamp, link, title, rawtext, summary, detailedtext, categorytags, legalorillegal, links, images, imagecaptions, imagetext, exifdata, emailid, cryptocoin, address, transactions, balance, ismalicious, virustotallink)

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
