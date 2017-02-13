git으로 파일을 다룰때 초기정보를 별도로 보관할 필요가 있다.
예를 들어 파일의 생성일자/수정일자 등 일자정보의 경우 clone 할 때, 유지할 수가 없다.

이를 해결하기 위해 별도의 meta정보를 저장하는 파일을 별도로 관리하여 필요한 정보를 유지할 수 있도록하는 것이
git_meta_store의 역할이다.