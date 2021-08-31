import requests
import json
import time
import datetime
import os

class Worker:
    def __init__(self, longitude, latitude, pickup_time, max_count):
        self._longitude = longitude
        self._latitude = latitude
        self._pickup_time = pickup_time
        self._max_count = max_count
        self._file_name = "output.txt"

    def run(self):
        if os.path.isfile(self._file_name):
            os.unlink(self._file_name)

        offset = 0
        fetch_count = 15

        while True:
            count = self._fetch_one_page(offset, fetch_count)
            if count == 0:
                break
            offset += fetch_count

            if offset >= self._max_count:
                break
        
        print("done")

    def _fetch_one_page(self, offset, fetch_count):
        url = self._generate_url_of_restaurant_list(offset, fetch_count)

        response = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
        })
        return self._process_one_page_of_restaurant_list(json.loads(response.text))

    def _generate_url_of_restaurant_list(self, offset, fetch_count):
        return "https://www.openrice.com/api/v2/search/themeListing?uiLang=zh&uiCity=hongkong&callName=takeaway&startAt=" + str(offset) + "&rows=" + str(fetch_count) + "&regionId=0&apiEntryPoint=21&geo=" + str(self._longitude) + "%2C" + str(self._latitude) + "&sortBy=Distance&districtId="

    def _process_one_page_of_restaurant_list(self, json):
        if "paginationResult" not in json or "results" not in json["paginationResult"]:
            return 0
        
        restaurant_list = json["paginationResult"]["results"]

        count = 0
        for restaurant in restaurant_list:
            print(restaurant["name"])

            obj = {
                "id": restaurant["poiId"],
                "name": restaurant["name"],
                "url": restaurant["takeAwayInfo"]["shortenUrl"],
                "time": restaurant["takeAwayInfo"]["infoDisplay"]
            }
            self._process_one_restaurant(obj)
            count += 1

        return count

    def _process_one_restaurant(self, restaurant):
        url = "https://www.openrice.com/api/v2/poi/" + str(restaurant["id"]) + "/takeaway/menu/-1?uiLang=zh&uiCity=hongkong&menuId=-1&pickupDate=" + self._pickup_time.strftime("%Y-%m-%d") + "&pickupTime=" + self._pickup_time.strftime("%H") + "%3A" + self._pickup_time.strftime("%M")
        response = requests.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36"
        })

        obj = json.loads(response.text)

        if "categories" not in obj:
            return
        
        with open(self._file_name, "a+", encoding="utf-8") as f:

            for cat in obj["categories"]:
                my_cat = {
                    "name": cat["name"],
                    "items": []
                }
                
                if "items" not in cat:
                    continue

                for item in cat["items"]:
                    my_item = {
                        "name": item["name"],
                        "price": item["unitPrice"]
                    }
                    if item["status"] == 3:
                        my_item["status"] = "暫不供應"
                    elif item["status"] == 5:
                        my_item["status"] = "售罄"
                    elif item["status"] == 10:
                        my_item["status"] = ""
                    else:
                        my_item["status"] = str(item["status"])

                    my_cat["items"].append(my_item)

                    f.write(restaurant["name"] + ",")
                    f.write(my_cat["name"] + ",")
                    f.write(my_item["name"] + ",")
                    f.write(str(my_item["price"]) + ",")
                    f.write(my_item["status"] + ",")
                    f.write(restaurant["url"])
                    f.write("\n")

def main():
    today = datetime.date.today()
    worker = Worker(22.278548, 114.1686556, datetime.datetime(today.year, today.month, today.day, 12, 45), 200)    #軍器廠街
    #worker = Worker(22.3828225, 114.2036165, datetime.datetime(today.year, today.month, today.day, 12, 45), 200)    #第一城站
    worker.run()

if __name__ == "__main__":
    main()
