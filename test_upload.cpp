#include <iostream>
#include <string>
#include <curl/curl.h>

int main() {
    // Инициализация libcurl
    CURL *curl = curl_easy_init();
    if (curl) {
        // URL сервера, на который отправляется запрос
        const char *url = "http://rusvs.istu.webappz.ru/solar/test/index.php";
        int number;
        std::cin>>number;
        std::string postData = "number=" + std::to_string(number);

        curl_easy_setopt(curl, CURLOPT_URL, url);
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, postData.c_str()); 

        curl_easy_setopt(curl, CURLOPT_VERBOSE, 1L);

        CURLcode res = curl_easy_perform(curl);
        if (res == CURLE_OK) {
            long response_code;
            curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &response_code);

            std::cout << "Запрос выполнен успешно. HTTP код: " << response_code << std::endl;
            
            if (response_code == 200) {
                std::cout << "Данные успешно отправлены!" << std::endl;
            } else {
                std::cout << "Ошибка на сервере. HTTP код: " << response_code << std::endl;
            }
        } else {
            std::cerr << "Ошибка при отправке запроса: " << curl_easy_strerror(res) << std::endl;
        }
        curl_easy_cleanup(curl);
    } else {
        std::cerr << "Не удалось инициализировать cURL!" << std::endl;
    }

    return 0;
}
