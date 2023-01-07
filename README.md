# payhere
[페이히어] Python 백엔드 엔지니어 과제 전형 (가계부)

프레임 워크 : Django

구현 기간 : 23/01/04 ~ 23/01/07 (4일)

## API & ERD 설계 의도
- 개인적으로 원하는 서비스 구도
<img src="https://user-images.githubusercontent.com/78214692/211133202-02b280ea-209b-4845-adaf-3b8e7773a04e.png" width=800px>

- **가게 사장님들의 가계부**를 만든다 생각했을 때, **달력과 함께 일별 수입/지출의 내역을 한눈에** 볼 수 있는 화면 구조를 생각하며 설계했습니다.
- 그러므로 지출뿐이 아니라 수입 기록도 가능하게 설계했습니다.
- **월 단위의 일별 수입/지출 정보들 & 상세 내역들을 보내주기 위해서 하루 내역(MoneyDayLog)과 상세 내역(MoneyDetailLog)를 1 : N의 관계로 구성하고 상세 내역의 변화에 있어, 하루 내역을 업데이트하는 구조로 설계하였습니다.**
- 카테고리를 추가함으로써 추후의 활용과 확장 가능성을 열어두었습니다.
- MoneyDayLog : 하루 내역 (특정 일자의 수입과 지출에 대한 정보)
- MoneyDetailLog : 상세 내역 (수입/지출, 카테고리, 금액, 메모)

<details>
<summary>ERD</summary>
<div markdown="1">


<img src="https://user-images.githubusercontent.com/78214692/211133965-a71c9301-20f0-424b-aef3-f2c4723bb4f3.png" width=800px>


</div>
</details>

<details>
<summary>API</summary>
<div markdown="1">

<br>

|Action| Method| URL|
|-----|----|----|
|회원가입| POST| /users/
|로그인| POST| /users/signin/
|로그 리스트| GET| /moneylogs/?date=
|로그 기록 작성| POST| /moneylogs/
|로그 상세| GET| /moneylogs/<int: pk>/
|로그 수정, 삭제, 복원| PUT| /moneylogs/<int: pk>/
|로그 영구 삭제| DELETE| /moneylogs/<int: pk>/
|공유 로그 접속| GET| /moneylogs/<int: pk>/share/
|로그 공유| POST| /moneylogs/<int: pk>/share/
|카테고리 리스트| GET| /moneylogs/category/
|카테고리 생성| POST| /moneylogs/category/
|카테고리 상세| GET| /moneylogs/category/<int: pk>/
|카테고리 수정| PUT| /moneylogs/category/<int: pk>/
|카테고리 삭제| DELETE| /moneylogs/category/<int: pk>/
<br>

</div>
</details>


## 요구 사항 구현 내용과 설명

### A. 가계부에 오늘 사용한 돈의 금액과 관련된 메모를 남길 수 있습니다.
- 수입/지출, 카테고리, 금액, 메모에 대하여 작성할 수 있습니다.
- 상세 내역의 수입/지출 금액을 하루 내역 정보에 추가합니다.

### B. 가계부에서 수정을 원하는 내역은 금액과 메모를 수정할 수 있습니다.
- 수입/지출에 대한 내용 금액, 메모, 카테고리를 변경 가능합니다.
- 상세 내역의 수입/지출에 대한 내용이 바뀐다면 하루 내역의 수입/지출 또한 업데이트가 되게 구현하였습니다.
- 로직
    1. 수정 전 상세 내역의 수입/지출 & 금액을 가지고 하루 내역의 수입/지출 정보에서 제거
    2. 수정된 상세 내역의 수입/지출 & 금액을 하루 내역의 수입/지출 정보에 합산
    
### C. 가계부에서 삭제를 원하는 내역은 삭제할 수 있습니다.
- **휴지통(soft_delete)으로** 이동하는 방식과 **복원, 영구 삭제(hard_delete)의** 방식으로 구현하였습니다.
- 휴지통 이동(soft_delte) or 복원
    - **delete 요청이 아닌 put요청**에서 **is_delete(bool)의** 값을 넘겨주어 휴지통으로 보낼지 복원할지 결정합니다.
    - 서비스 사용 시, 휴지통 이동 혹은 복원 요청에서 is_delete 값 외에 정보는 들어오지 않겠지만 들어온다 하더라도 **is_delete 값이 들어온다면 is_delete에 대한 정보만 변경**하도록 구현하였습니다.
    - 휴지통 이동/복원 시에도 마찬가지로, 하루 내역의 수입/지출에 대한 정보도 업데이트해줍니다.
- 영구 삭제(hard_delete)
    - 휴지통 -> 영구 삭제의 순서로 서비스가 돌아갈 것이기에 단순하게 삭제를 합니다.
    - 휴지통으로 이동 시에 하루 내역의 수입/지출의 정보를 업데이트해주므로 따로 변경되는 것은 없으나
    - 이를 대비한다면 is_delete 값을 확인하여 거절 혹은 업데이트할 수 있을 것입니다.
<details>
<summary>B & C 코드</summary>
<div markdown="1">

```python
def perform_update(self, serializer):
  """
  되돌렸던 수입/지출의 값에 새로 들어온 금액을 업데이트 해줍니다.
  """
  with transaction.atomic():
      instance = serializer.save()
      self.add_income_expense(instance)
      instance.day_log.save()
      
def update(self, request, *args, **kwargs):
  """
  put request 요청에서 is_delete 값의 포함 여부에 따라
  soft_delete|복원과 partial_update로 나뉩니다.(soft_delete 우선순위)
  soft-delete : is_delete 값이 True라면 삭제이고 False라면 복원입니다.
              그에 따라 일별 총 수입/지출의 값을 바꿔줍니다.
  update : 이전 상세 기록의 수입/지출을 참조하여 일별 수입/지출을 되돌린 후 업데이트된 값으로 대체합니다.
              이후 상세 기록의 값을 업데이트해줍니다.
  """
  partial = kwargs.pop('partial', False)
  instance = self.get_object()
  serializer = self.get_serializer(instance, data=request.data, partial=partial)
  serializer.is_valid(raise_exception=True)
  is_delete = serializer.validated_data.get('is_delete', '')

  if is_delete != '' and instance.is_delete != is_delete:
      if is_delete:
          data = '휴지통 이동'
          self.sub_income_expense(instance)
      else:
          data = MoneyDetailLogSerializer(instance).data
          self.add_income_expense(instance)
      instance.is_delete = is_delete

      with transaction.atomic():
          instance.save()
          instance.day_log.save()
      return Response(data, status=status.HTTP_200_OK)


  self.sub_income_expense(instance) # 업데이트를 위한 되돌림
  self.perform_update(serializer)

  if getattr(instance, '_prefetched_objects_cache', None):
      instance._prefetched_objects_cache = {}
  return Response(serializer.data)
```

</div>
</details>
  
### D. 가계부에서 이제까지 기록한 가계부 리스트를 볼 수 있습니다.
- 일별 수입/지출 정보와 상세 리스트를 **월 단위**로 제공합니다.
  <details>
  <summary>월 단위 리스트 코드</summary>
  <div markdown="1">

  ```python
  def list(self, request, *args, **kwargs):
      """월별로 데이터를 제공합니다. 데이터를 제공합니다.

      query_string에는 date가 들어오며 default 값으로는 오늘 날짜입니다. (ex. 2022-02-11)
      money_day_logs : 이번 달의 각 일별 수입/지출 리스트
      money_detail_logs : 이번 달의 전체 로그 리스트
      """
      user = request.user
      today = datetime.today().date()
      date = request.query_params.get('date', str(today))

      start_date_time, end_date_time = get_date_range(date)

      day_q = Q(date__gte=start_date_time.date()) & Q(date__lte=end_date_time.date()) & Q(user_id=user.id)
      detail_q = Q(day_log__date__gte=start_date_time.date()) & Q(day_log__date__lte=end_date_time.date()) \
                & Q(user_id=user.id) & Q(is_delete=False)

      money_day_logs = MoneyDayLog.objects.select_related('user').filter(day_q).order_by('date')
      money_detail_logs = MoneyDetailLog.objects.select_related('user', 'day_log', 'day_log__user')\
                      .filter(detail_q).annotate(date=F("day_log__date")).order_by('date', '-updated_at')
      queryset = {
          'money_day_logs' : money_day_logs,
          'money_detail_logs' : money_detail_logs
      }

      serializer = self.get_serializer(queryset)
      return Response(serializer.data)
  ```

  </div>
  </details>
### E. 가계부에서 상세한 세부 내역을 볼 수 있습니다.
- 하나의 상세 내역을 가져옵니다.

### F. 가계부의 세부 내역을 복제할 수 있습니다.
- 자신의 특정 상세 내역을 복제할 수 있습니다.
- 복제한 상세 내역의 수입/지출의 금액 정보를 하루 내역의 수입/지출에 업데이트합니다.
  <details>
  <summary>복제  코드</summary>
  <div markdown="1">

  ```python
  @action(detail=True, methods=['post'])
  def copy_log(self, request, pk=None):
      """로그를 복사하는 메서드
      """
      instance = self.get_object()
      instance.pk = None
      self.add_income_expense(instance)

      with transaction.atomic():
          instance.save()
          instance.day_log.save()
      return Response(status=status.HTTP_200_OK)
  ```

  </div>
  </details>

### G. 가계부의 특정 세부 내역을 공유할 수 있게 단축 URL을 만들 수 있습니다. (단축 URL은 특정 시간 뒤에 만료되어야 합니다.)
- 초기 설계
    - 상세 내역의 정보를 담은 딕셔너리를 암호화한 값을 url로 저장하고 반환합니다.
    - 입장 시에는 복호화 한 값의 정보를 통해 데이터 전달/거절을 합니다.
- 트러블
    - 암호화한 값에 "/"가 들어가게 되어 잘못된 경로 에러 발생
- 변경 설계 & 구현
    - 공유 시에 해당 게시글의 공유 기한을 정합니다.
    - 접속 시에는 공유 기한을 넘지 않은 상세 내역을 요청합니다.
    - 없을 시에는 404를 반환합니다.

<!-- - 변경될 내용
    - 다른 암호화&복호화 라이브러리를 찾아서 초기 설계대로 구현할 예정
    - 그렇게 되면 기존 /moneylogs/<int: pk>/share/ 에서 2개의 request methods를 처리하였는데 나뉘게 될 것으로 예상됩니다. -->

<details>
<summary>공유 & 접근 코드</summary>
<div markdown="1">

```python
@action(detail=True, methods=['post'])
def make_link(self, request, pk=None):
    """금전 로그 공유 url설정 메서드
    """
    share_limit = datetime.now() + relativedelta(hours=24)
    instance = self.get_object()
    instance.share_limit = share_limit
    instance.save()
    return Response(status=status.HTTP_200_OK)

@action(detail=True, methods=['get'])
def enter_link(self, request, pk=None):
    """공유된 로그의 정보 제공 메서드
    """
    instance = get_object_or_404(MoneyDetailLog, pk=pk, share_limit__gte=datetime.now())
    serializer = MoneyDetailLogSerializer(instance)
    return Response(serializer.data, status=status.HTTP_200_OK)
```

</div>
</details>
  
### 로그인하지 않은 고객은 가계부 내역에 대한 접근 제한 처리가 되어야 합니다.
- JWT 로그인이 됐는지 확인을 먼저 합니다. (이메일, 비밀번호-암호화)
- 또한 가계부의 특성상 기본적으로 자신만이 확인이 가능하므로 기본 queryset은
- 자신의 기록들만 가져옵니다.

<details>
<summary>코드</summary>
<div markdown="1">

```python
def get_queryset(self):
    """base가 되는 queryset

    현재 로그인한 유저의 MoneyDetailLog를 가져옵니다.
    """
    user_id = self.request.user.id
    return MoneyDetailLog.objects.filter(user_id=user_id)
```

</div>
</details>

### 카테고리
- 자신만의 카테고리를 읽기/생성/수정/삭제가 가능합니다

#### 읽기
- 글을 작성할 때 자신이 선택할 카테고리의 정보를 보내주기 위한 API

#### 생성
- 같은 이름의 카테고리 여부를 판단하고 생성합니다.

#### 삭제
- 해당 카테고리를 바라보는 상세 내역의 카테고리 정보를 **전부 None으로 바꾼 후** 삭제합니다.

<details>
<summary>카테고리 기능 코드</summary>
<div markdown="1">

```python
class CategoryModelViewSet(ModelViewSet):
    serializer_class = MoneyCategorySerializer
    permission_classes = [permissions.IsAuthenticated,]

    def get_queryset(self):
        """base가 되는 queryset

        현재 로그인한 유저의 MoneyCategory를 가져옵니다.
        """
        user_id = self.request.user.id
        return MoneyCategory.objects.filter(user_id=user_id)
    
    def create(self, request, *args, **kwargs):
        """
        카테고리 생성 메서드 (중복 방지)
        """
        name = request.data.get('name', '')
        user = self.request.user
        if MoneyCategory.objects.filter(user=user, name=name).exists():
            return Response({"message" : "이미 존재하는 카테고리입니다."},status=status.HTTP_409_CONFLICT)
        return super().create(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        user = self.request.user
        serializer.save(user=user)

    def destroy(self, request, *args, **kwargs):
        """
        해당 카테고리를 참조하는 MoneyDetailLog들의 카테고리를 없애고
        카테고리를 지웁니다.
        """
        instance = self.get_object()
        instance.detail_logs.update(category=None)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
```

</div>
</details>


### 테스트 코드
- 상세 내역들의 생성/삭제/복원에 따른 일별 수입/지출과의 일치 여부 테스트가 우선순위로 생각하여 먼저 구현하였습니다. (복제, 수정 시 테스트 케이스 추가 필요)
- 외 상세 내역의 접근과 생성 등 8개의 테스트 케이스 구현하였습니다. (추가 필요)
