from utils.common_util import SnakeCaseUtil


class TestSnakeCaseUtil:
    """
    小驼峰形式(camelCase)转下划线形式(snake_case)工具方法
    """

    @classmethod
    def test_camel_to_snake(cls):
        """
        小驼峰形式字符串(camelCase)转换为下划线形式字符串(snake_case)

        :param camel_str: 小驼峰形式字符串
        :return: 下划线形式字符串
        """
        # 在大写字母前添加一个下划线，然后将整个字符串转为小写

        assert (
            SnakeCaseUtil.camel_to_snake(camel_str="testCamelCase") == "test_camel_case"
        )

        assert (
            SnakeCaseUtil.camel_to_snake(camel_str="test_camel_case") == "test_camel_case"
        )
    
        assert (
            SnakeCaseUtil.camel_to_snake(camel_str="TestCamelCase") == "test_camel_case"
        )