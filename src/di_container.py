"""
DI Container - CLEAN 아키텍처 의존성 주입 컨테이너

🔄 IoC (Inversion of Control) Container:
========================================
모든 의존성을 중앙에서 관리하고 주입하여 완전한 CLEAN 아키텍처를 구현합니다.
각 클래스는 구체적인 구현체를 알 필요 없이 Interface만 요청하면 됩니다.

🎯 핵심 기능:
============
- Singleton 패턴: 단일 인스턴스 보장
- Transient 패턴: 매번 새로운 인스턴스
- 순환 의존성 감지 및 방지
- 자동 생성자 주입 (Constructor Injection)
- 런타임 의존성 해결 (Runtime Resolution)

📐 확장성:
==========
- 새로운 서비스 추가 시 기존 코드 수정 불필요
- Factory 패턴 지원으로 복잡한 객체 생성
- Decorator 패턴으로 횡단 관심사 적용 가능
"""

import inspect
import logging
from typing import Type, Any, Dict, Set, Callable, Optional, get_origin, get_args
from threading import RLock

from interfaces import IDependencyContainer

logger = logging.getLogger(__name__)


class DependencyInjectionContainer(IDependencyContainer):
    """
    CLEAN 아키텍처용 의존성 주입 컨테이너

    🏗️ 아키텍처 핵심:
    ==================
    모든 레이어간 의존성을 이 컨테이너가 관리합니다.
    - Presentation Layer → Application Layer
    - Application Layer → Domain Layer
    - Domain Layer → Infrastructure Layer

    🔒 스레드 안전성:
    ================
    멀티스레드 환경에서도 안전한 의존성 해결을 보장합니다.
    """

    def __init__(self):
        """컨테이너 초기화"""
        self._services: Dict[Type, Any] = {}  # 등록된 서비스들
        self._singletons: Dict[Type, Any] = {}  # 싱글톤 인스턴스들
        self._factories: Dict[Type, Callable] = {}  # 팩토리 함수들
        self._resolution_stack: Set[Type] = set()  # 순환 의존성 감지용
        self._lock = RLock()  # 스레드 안전성 보장

        logger.info("DI Container 초기화 완료")

    def register_singleton(self, interface: Type, implementation: Type) -> None:
        """
        서비스를 싱글톤으로 등록

        🔒 싱글톤 패턴:
        ==============
        한 번 생성된 인스턴스를 계속 재사용합니다.
        데이터베이스 연결, 설정 관리, 로깅 서비스 등에 적합합니다.

        Args:
            interface: 추상 인터페이스 타입
            implementation: 구체적인 구현체 타입
        """
        with self._lock:
            self._validate_registration(interface, implementation)

            self._services[interface] = {
                'implementation': implementation,
                'lifetime': 'singleton',
                'instance': None
            }

            logger.debug(f"싱글톤 서비스 등록: {interface.__name__} -> {implementation.__name__}")

    def register_transient(self, interface: Type, implementation: Type) -> None:
        """
        서비스를 Transient로 등록

        🔄 Transient 패턴:
        ==================
        매번 새로운 인스턴스를 생성합니다.
        상태를 가지지 않는 서비스나 요청별 독립성이 필요한 경우에 적합합니다.

        Args:
            interface: 추상 인터페이스 타입
            implementation: 구체적인 구현체 타입
        """
        with self._lock:
            self._validate_registration(interface, implementation)

            self._services[interface] = {
                'implementation': implementation,
                'lifetime': 'transient',
                'instance': None
            }

            logger.debug(f"Transient 서비스 등록: {interface.__name__} -> {implementation.__name__}")

    def register_factory(self, interface: Type, factory: Callable) -> None:
        """
        팩토리 함수로 서비스 등록

        🏭 Factory 패턴:
        ===============
        복잡한 초기화 로직이 필요한 객체를 위한 사용자 정의 생성 로직입니다.

        Args:
            interface: 인터페이스 타입
            factory: 인스턴스를 생성하는 팩토리 함수
        """
        with self._lock:
            if not callable(factory):
                raise ValueError(f"Factory must be callable: {factory}")

            self._factories[interface] = factory
            logger.debug(f"팩토리 서비스 등록: {interface.__name__}")

    def resolve(self, interface: Type) -> Any:
        """
        의존성 해결 및 인스턴스 반환

        🔍 해결 과정:
        ============
        1. 순환 의존성 검사
        2. 등록된 서비스 확인
        3. Singleton 인스턴스 확인
        4. 생성자 의존성 분석 및 재귀 해결
        5. 인스턴스 생성 및 캐싱

        Args:
            interface: 요청할 인터페이스 타입

        Returns:
            해결된 서비스 인스턴스

        Raises:
            ValueError: 등록되지 않은 서비스
            RuntimeError: 순환 의존성 감지
        """
        with self._lock:
            # 1. 순환 의존성 감지
            if interface in self._resolution_stack:
                cycle = " -> ".join([cls.__name__ for cls in self._resolution_stack])
                cycle += f" -> {interface.__name__}"
                raise RuntimeError(f"순환 의존성 감지: {cycle}")

            self._resolution_stack.add(interface)

            try:
                # 2. 팩토리 함수 우선 확인
                if interface in self._factories:
                    logger.debug(f"팩토리로 해결: {interface.__name__}")
                    return self._factories[interface]()

                # 3. 등록된 서비스 확인
                if interface not in self._services:
                    raise ValueError(f"등록되지 않은 서비스: {interface.__name__}")

                service_config = self._services[interface]
                implementation = service_config['implementation']
                lifetime = service_config['lifetime']

                # 4. 싱글톤 인스턴스 확인
                if lifetime == 'singleton':
                    if service_config['instance'] is not None:
                        logger.debug(f"싱글톤 인스턴스 재사용: {interface.__name__}")
                        return service_config['instance']

                # 5. 새 인스턴스 생성
                instance = self._create_instance(implementation)

                # 6. 싱글톤 캐싱
                if lifetime == 'singleton':
                    service_config['instance'] = instance

                logger.debug(f"서비스 해결 완료: {interface.__name__} ({lifetime})")
                return instance

            finally:
                self._resolution_stack.discard(interface)

    def _create_instance(self, implementation: Type) -> Any:
        """
        생성자 의존성 주입으로 인스턴스 생성

        🔧 자동 주입:
        ============
        생성자의 타입 힌트를 분석하여 필요한 의존성을 자동으로 주입합니다.

        Args:
            implementation: 생성할 클래스 타입

        Returns:
            의존성이 주입된 인스턴스
        """
        # 생성자 시그니처 분석
        signature = inspect.signature(implementation.__init__)
        parameters = signature.parameters

        # 첫 번째 매개변수(self) 제외
        param_names = list(parameters.keys())[1:]

        if not param_names:
            # 의존성이 없는 경우
            logger.debug(f"의존성 없는 인스턴스 생성: {implementation.__name__}")
            return implementation()

        # 의존성 해결
        dependencies = {}
        for param_name in param_names:
            param = parameters[param_name]

            if param.annotation == param.empty:
                raise ValueError(
                    f"생성자 매개변수에 타입 힌트가 필요합니다: "
                    f"{implementation.__name__}.{param_name}"
                )

            # Optional 타입 처리
            param_type = param.annotation
            if get_origin(param_type) is type(Optional[int]) or str(param_type).startswith('typing.Union'):
                # Optional[T] = Union[T, None]처리
                args = get_args(param_type)
                if len(args) == 2 and type(None) in args:
                    # None이 아닌 실제 타입 찾기
                    param_type = args[0] if args[1] is type(None) else args[1]
                    # Optional 매개변수는 None으로 설정
                    dependencies[param_name] = None
                    continue

            # 재귀적으로 의존성 해결
            dependency = self.resolve(param_type)
            dependencies[param_name] = dependency

        logger.debug(
            f"의존성 주입으로 인스턴스 생성: {implementation.__name__} "
            f"({len(dependencies)}개 의존성)"
        )

        return implementation(**dependencies)

    def is_registered(self, interface: Type) -> bool:
        """
        서비스 등록 여부 확인

        Args:
            interface: 확인할 인터페이스 타입

        Returns:
            등록 여부
        """
        with self._lock:
            return (interface in self._services or
                   interface in self._factories)

    def get_registered_services(self) -> Dict[str, str]:
        """
        등록된 모든 서비스 목록 조회

        Returns:
            서비스 목록 (인터페이스 -> 구현체)
        """
        with self._lock:
            services = {}

            for interface, config in self._services.items():
                services[interface.__name__] = {
                    'implementation': config['implementation'].__name__,
                    'lifetime': config['lifetime'],
                    'has_instance': config['instance'] is not None
                }

            for interface in self._factories:
                services[interface.__name__] = {
                    'implementation': 'Factory Function',
                    'lifetime': 'factory',
                    'has_instance': False
                }

            return services

    def clear(self) -> None:
        """
        모든 등록된 서비스 및 인스턴스 제거

        🧹 정리:
        ========
        테스트나 애플리케이션 종료 시 사용합니다.
        """
        with self._lock:
            self._services.clear()
            self._singletons.clear()
            self._factories.clear()
            self._resolution_stack.clear()
            logger.info("DI Container 초기화됨")

    def _validate_registration(self, interface: Type, implementation: Type) -> None:
        """
        서비스 등록 유효성 검증

        Args:
            interface: 인터페이스 타입
            implementation: 구현체 타입

        Raises:
            ValueError: 유효하지 않은 등록
        """
        if not inspect.isclass(interface):
            raise ValueError(f"Interface must be a class: {interface}")

        if not inspect.isclass(implementation):
            raise ValueError(f"Implementation must be a class: {implementation}")

        # 인터페이스 상속 확인 (ABC의 경우)
        if hasattr(interface, '__abstractmethods__'):
            if not issubclass(implementation, interface):
                raise ValueError(
                    f"구현체가 인터페이스를 구현하지 않음: "
                    f"{implementation.__name__} does not implement {interface.__name__}"
                )

    def __repr__(self) -> str:
        """컨테이너 상태 표시"""
        with self._lock:
            service_count = len(self._services)
            factory_count = len(self._factories)
            singleton_instances = sum(
                1 for config in self._services.values()
                if config['lifetime'] == 'singleton' and config['instance'] is not None
            )

            return (
                f"DIContainer(services={service_count}, factories={factory_count}, "
                f"active_singletons={singleton_instances})"
            )