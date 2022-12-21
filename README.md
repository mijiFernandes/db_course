# db_course

22/12/20 12:30 시점 Django model 없이 Raw SQL로 전부 대체


**DB 등록 시에 TABLE_COUNTS라는 전체 테이블 관리 테이블 생성

![슬라이드6](https://user-images.githubusercontent.com/99490528/208578085-f17fd575-f947-4037-ba15-3214c630985c.PNG)


**CSV 파일 업로드 시에 해당 CSV파일 정보를 바탕으로 한 테이블 생성 후 TABLE_COUNTS 테이블에도 필요 정보 등록

![슬라이드7](https://user-images.githubusercontent.com/99490528/208578160-fedfc037-8d41-4198-842a-1f8f3c824095.PNG)


**현재 전체적인 동작과정

![슬라이드8](https://user-images.githubusercontent.com/99490528/208578318-1127e2e3-fffb-4feb-a0b1-1cdad26f55b2.PNG)
