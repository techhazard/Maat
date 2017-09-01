import sys
import uuid
import unittest

from hypothesis import given
import hypothesis.strategies as st

from deepdiff import DeepDiff as ddiff

from validation import uuid_validation
from validation import maat_scale, Invalid
from validation import int_validation, str_validation, float_validation, list_validation, dict_validation

from extras import validate_args


class TestValidation(unittest.TestCase):

    def setUp(self):
        self.test_input = {
            'id': 23,
            'name': 'John Doe',
            'type': 'banana',
        }
        self.test_validation = {
            'id': {'validator': 'int', 'args': {'min_amount': 1}},
            'name': {'validator': 'str', 'args': {'min_length': 1, 'max_length': 35, 'regex': r'(\w+ )(\w+)'}},
            'type': {'validator': 'str', 'args': {'choices': ['apple', 'banana', 'citrus']}}
        }

    def test_validation(self):
        """Happy path test"""
        validated_items = maat_scale(self.test_input, self.test_validation)
        difference = ddiff(validated_items, self.test_input)

        # if the differ finds no difference a empty dictionary is returned
        self.assertEqual(difference, {})

    def test_validation_test_invalid_keys_exception(self):
        """Test invalid keys exception"""

        del self.test_input['type']

        with self.assertRaisesRegexp(Invalid, 'type: missing key'):
            _ = maat_scale(self.test_input, self.test_validation)

    def test_validation_test_remove_key_and_set_optional(self):
        """Test remove key and set optional"""

        del self.test_input['type']
        self.test_validation['type']['optional'] = True

        validated_items = maat_scale(self.test_input, self.test_validation)
        difference = ddiff(validated_items, self.test_input)
        self.assertEqual(difference, {})

    def test_validation_test_remove_key_and_remove_required(self):
        """Test remove key and set optional"""

        del self.test_input['type']
        self.test_validation['type']['optional'] = True
        excepted_value = 'banana'
        self.test_validation['type']['default_value'] = excepted_value

        validated_items = maat_scale(self.test_input, self.test_validation)
        difference = ddiff(validated_items, self.test_input)
        self.assertEqual(difference, {'dictionary_item_removed': set(["root['type']"])})
        self.assertEqual(validated_items['type'], excepted_value)

    def test_validation_test_remove_key_and_set_default(self):
        """Test remove key and set optional"""

        del self.test_input['type']
        excepted_value = 'banana'
        self.test_validation['type']['default_value'] = excepted_value

        validated_items = maat_scale(self.test_input, self.test_validation)
        difference = ddiff(validated_items, self.test_input)
        self.assertEqual(difference, {'dictionary_item_removed': set(["root['type']"])})
        self.assertEqual(validated_items['type'], excepted_value)

    def test_validate_invalid_id(self):
        """Set id to invalid value, expect Exception"""
        self.test_input['id'] = -1

        with self.assertRaisesRegexp(Invalid, 'id contains invalid item -1: integer is less then 1'):
            _ = maat_scale(self.test_input, self.test_validation)

    def test_validate_invalid_int_value_name(self):
        self.test_input['name'] = 30
        with self.assertRaisesRegexp(Invalid, 'name contains invalid item 30: not of type string'):
            _ = maat_scale(self.test_input, self.test_validation)

        # test validator of name to make the previous invalid value valid.
        self.test_validation['name'] = {'validator': 'int'}
        validated_items = maat_scale(self.test_input, self.test_validation)
        difference = ddiff(validated_items, self.test_input)
        self.assertEqual(difference, {})

    def test_validate_(self):
        self.test_input['name'] = 30
        with self.assertRaisesRegexp(Invalid, 'name contains invalid item 30: not of type string'):
            _ = maat_scale(self.test_input, self.test_validation)

        # test validator of name to make the previous invalid value valid.
        self.test_validation['name'] = {'validator': 'int'}
        validated_items = maat_scale(self.test_input, self.test_validation)
        difference = ddiff(validated_items, self.test_input)
        self.assertEqual(difference, {})

    def test_validate_nested_dict(self):
        self.test_input = {
            'id': 23,
            'addresses': {
                'street': 'John Doe Street',
                'number': 123,
            }
        }
        self.test_validation = {
            'id': {'validator': 'int', 'args': {'min_amount': 1}},
            'addresses': {'validator': 'dict', 'args': {'key_regex': r'(\w+ )'}, 'nested': {
                'street': {'validator': 'str', 'args': {'min_length': 5, 'max_length': 99}},
                'number': {'validator': 'int', 'args': {'min_amount': 1}}}
            }
        }
        validated_items = maat_scale(self.test_input, self.test_validation)
        difference = ddiff(validated_items, self.test_input)
        self.assertEqual(difference, {})

    def test_validate_nested_list(self):
        self.test_input = {
            'id': 23,
            'addresses': [
                {'street': 'John Doe Street'},
                {'street': 'John Doe Street'},
                {'street': 'John Doe Street'},
                {'street': 'John Doe Street'},
            ]
        }
        self.test_validation = {
            'id': {'validator': 'int', 'args': {'min_amount': 1}},
            'addresses': {'validator': 'list', 'args': {},
                'list_dicts': {
                    'street': {'validator': 'str', 'args': {'min_length': 5, 'max_length': 99},},
                }
            }
        }

        validated_items = maat_scale(self.test_input, self.test_validation)
        difference = ddiff(validated_items, self.test_input)
        self.assertEqual(difference, {})

    def test_validate_two_deep_nested_dict(self):
        self.test_input = {
            'id': 23,
            'addresses': {
                'street': {
                    'two': 'deep',
                }
            }
        }
        self.test_validation = {
            'id': {'validator': 'int', 'args': {'min_amount': 1}},
            'addresses': {'validator': 'dict', 'args': {'key_regex': r'(\w+ )'},
                'nested': {
                    'street': {'validator': 'dict', 'args': {'min_amount': 5, 'max_length': 99},
                        'nested': {
                            'two': {'validator': 'str', 'args': {'min_length': 3, 'max_length': 99}},
                        }
                    }
                }
            }
        }
        validated_items = maat_scale(self.test_input, self.test_validation)
        difference = ddiff(validated_items, self.test_input)
        self.assertEqual(difference, {})

    def test_validate_very_nested_dict(self):
        nested_dict = {
            'data': {
                'people': {
                    '7': {
                        'id': 7,
                        'name': 'John Doe',
                        'type': 'mimic',
                        'x': 823.6228647149701,
                        'y': 157.57736006592654,
                        'address': {
                            'id': 23,
                            'addresses': {
                                'street': {
                                    'two': 'deep',
                                    '222': 'deep',
                                }
                            }
                        }
                    },
                    '208': {
                        'id': 208,
                        'name': 'John Doe Too',
                        'type': 'person',
                        'x': 434.9446032612515,
                        'y': 580.0,
                        'address': {
                            'id': 23,
                            'addresses': {
                                'street': {
                                    'two': 'deep',
                                    '222': 'deep',
                                }
                            }
                        }
                    }
                },
                'streets': {
                    'id': 23,
                    'addresses': [
                        {'street': 'John Doe Street'},
                        {'street': 'John Doe Street'},
                        {'street': 'John Doe Street'},
                        {'street': 'John Doe Street'},
                    ]
                }
            }
        }
        addresses_item = {
            'id': {'validator': 'int', 'args': {'min_amount': 1}},
            'addresses': {'validator': 'list', 'args': {}, 'nested': {
                'street': {'validator': 'dict', 'args': {'min_amount': 5, 'max_length': 99}, 'nested': {
                    'two': {'validator': 'str', 'args': {'min_length': 3, 'max_length': 99}},
                    '222': {'validator': 'str', 'args': {'min_length': 3, 'max_length': 99}},
                        }
                    }
                }
            }
        }

        geo_item = {
            'id': {'validator': 'int', 'args': {'min_amount': 1}},
            'name': {'validator': 'str', 'args': {'min_length': 1, 'max_length': 35, 'regex': '([^\s]+)'}},
            'type': {'validator': 'str', 'args': {'min_length': 1, 'max_length': 25, 'regex': r'([^\s]+)'}},
            'x': {'validator': 'float'},
            'y': {'validator': 'float'},
            'address': {'validator': 'dict',
                'nested': addresses_item}
        }

        nested_dict_validation = {
            'data': {'validator': 'dict', 'nested': {
                'people': {'validator': 'dict', 'args': {'min_amount': 1, 'max_amount': 99}, 'aso_array': True,
                    'nested': geo_item},
                'streets': {'validator': 'dict', 'nested': {
                    'id': {'validator': 'int', 'args': {'min_amount': 1}},
                    'addresses': {'validator': 'list', 'list_dicts': True, 'nested': {
                        'street': {'validator': 'str', 'args': {'min_length': 1, 'max_length': 99}}}
                            }
                        }
                    }
                }
            }
        }
        validated_items = maat_scale(nested_dict, nested_dict_validation)
        difference = ddiff(validated_items, nested_dict)
        self.assertEqual(difference, {})

    def test_validate_very_nested_dict_fail_lowest_item(self):
        nested_dict = {
            'data': {
                'people': {
                    '7': {
                        'id': 7,
                        'name': 'John Doe',
                        'type': 'mimic',
                        'x': 823.6228647149701,
                        'y': 157.57736006592654,
                        'address': {
                            'id': 23,
                            'addresses': {
                                'street': {
                                    'two': 'deep',
                                    '222': 'deep',
                                }
                            }
                        }
                    },
                    '208': {
                        'id': 208,
                        'name': 'John Doe Too',
                        'type': 'person',
                        'x': 434.9446032612515,
                        'y': 580.0,
                        'address': {
                            'id': 23,
                            'addresses': {
                                'street': {
                                    'two': 'deep',
                                    '222': 'deep',
                                }
                            }
                        }
                    }
                },
                'streets': {
                    'id': 23,
                    'addresses': [
                        {'street': 'John Doe Street'},
                        {'street': 'John Doe Street'},
                        {'street': 'John Doe Street'},
                        {'street': 'John Doe Street'},
                    ]
                }
            }
        }
        addresses_item = {
            'id': {'validator': 'int', 'args': {'min_amount': 1}},
            'addresses': {'validator': 'list', 'args': {}, 'nested': {
                'street': {'validator': 'dict', 'args': {'min_amount': 5, 'max_length': 99}, 'nested': {
                    'two': {'validator': 'str', 'args': {'min_length': 3, 'max_length': 99}},
                    '222': {'validator': 'str', 'args': {'min_length': 3, 'max_length': 99, 'choices': [
                        'not_part_of_choices',
                        'fail_here']}},
                        }
                    }
                }
            }
        }

        geo_item = {
            'id': {'validator': 'int', 'args': {'min_amount': 1}},
            'name': {'validator': 'str', 'args': {'min_length': 1, 'max_length': 35, 'regex': '([^\s]+)'}},
            'type': {'validator': 'str', 'args': {'min_length': 1, 'max_length': 25, 'regex': r'([^\s]+)'}},
            'x': {'validator': 'float'},
            'y': {'validator': 'float'},
            'address': {'validator': 'dict',
                'nested': addresses_item}
        }

        nested_dict_validation = {
            'data': {'validator': 'dict', 'nested': {
                'people': {'validator': 'dict', 'args': {'min_amount': 1, 'max_amount': 99}, 'aso_array': True,
                    'nested': geo_item},
                'streets': {'validator': 'dict', 'nested': {
                    'id': {'validator': 'int', 'args': {'min_amount': 1}},
                    'addresses': {'validator': 'list', 'list_dicts': True, 'nested': {
                        'street': {'validator': 'str', 'args': {'min_length': 1, 'max_length': 99}}}
                            }
                        }
                    }
                }
            }
        }
        exp_exc_msg = "222 contains invalid item deep: not in valid choices \['not_part_of_choices', 'fail_here'\]"
        with self.assertRaisesRegexp(Invalid, exp_exc_msg):
            _ = maat_scale(nested_dict, nested_dict_validation)


class TestValidatorPropertyBased(unittest.TestCase):

    def result_as_bool(self, func, *args, **kwargs):
        try:
            func(*args, **kwargs)
        except Invalid:
            return False

        return True

    @given(val=st.text(), min_length=st.integers(), max_length=st.integers())
    def test_string_size_validation_test(self, val, min_length, max_length):
        expected = (max_length +1) > len(val) > (min_length -1)
        result = self.result_as_bool(str_validation, val=val, min_length=min_length, max_length=max_length)
        self.assertEqual(expected, result)

    @given(val=st.integers(), min_amount=st.integers(min_value=(-sys.maxint), max_value=sys.maxint),
           max_amount=st.integers(min_value=(-sys.maxint), max_value=sys.maxint))
    def test_int_validation_min_max(self, val, min_amount, max_amount):
        expected = val <= max_amount and val >= min_amount
        result = self.result_as_bool(int_validation, val=val, min_amount=min_amount, max_amount=max_amount)

        self.assertEqual(expected, result)

    #TODO Python long ints to float conversion goes wrong, thus all tests too.
    @given(val=st.floats(), min_amount=st.integers(min_value=(-sys.maxint), max_value=sys.maxint),
           max_amount=st.integers(min_value=(-sys.maxint), max_value=sys.maxint).filter(lambda x: x != 0))
    def test_float_validation_min_max(self, val, min_amount, max_amount):
        expected = val < max_amount and val >= min_amount
        result = self.result_as_bool(float_validation, val=val, min_amount=min_amount, max_amount=max_amount)

        self.assertEqual(expected, result)

    # def list_validation_size_test(self):
    #     pass


class ValidatorTests(unittest.TestCase):

    def test_str_validation_untouched_test(self):
        expected = 'banana'
        result = str_validation(val=expected)
        self.assertEqual(expected, result)

    def test_str_validation_min_length(self):
        expected = '1234'
        result = str_validation(val=expected, min_length=4)
        self.assertEqual(expected, result)

    def test_str_validation_min_length_failed(self):
        expected = '123'
        with self.assertRaises(Invalid):
            _ = str_validation(val=expected, min_length=4)

    def test_validation_max_length(self):
        expected = '1234'
        result = str_validation(val=expected, max_length=4)
        self.assertEqual(expected, result)

    def test_str_validation_max_length_failed(self):
        expected = '12345'
        with self.assertRaises(Invalid):
            _ = str_validation(val=expected, max_length=4)

    def test_str_validation_reqex_test(self):
        """Match only two words with regex"""
        regex = r'^(\w+ )(\w+)$'
        expected = 'apple tree'
        result = str_validation(val=expected, regex=regex)
        self.assertEqual(expected, result)

    def test_str_validation_failed_regex_test(self):
        """Match only two words with regex"""
        regex = r'^(\w+ )(\w+)$'
        expected = 'apple tree barks what is '
        with self.assertRaises(Invalid):
            _ = str_validation(key=None, val=expected, regex=regex)

    def test_str_validation_choices_test(self):
        expected = ['apple', 'banana', 'citrus']
        for item in expected:
            result = str_validation(val=item, choices=expected)
            self.assertEqual(item, result)

    def test_str_validation_choices_wrong_item_test(self):
        choices = ['apple', 'banana', 'citrus']
        wrong_choices = ['star', 'moon']
        for item in wrong_choices:
            with self.assertRaises(Invalid):
                _ = str_validation(val=item, choices=choices)

    def test_int_validation_convert_to_int_test(self):
        expected = '5'
        with self.assertRaises(Invalid):
            _ = int_validation(val=expected)

        result = int_validation(val=expected, cast=True)
        self.assertEqual(int(expected), result)

    def test_int_validation_convert_fail_test(self):
        expected = 'appel'
        with self.assertRaises(Invalid):
            _ = int_validation(val=expected)

        with self.assertRaises(Invalid):
            _ = int_validation(val=expected, cast=True)

    def test_float_validation_convert_to_float_test(self):
        expected = '5'
        with self.assertRaises(Invalid):
            _ = float_validation(val=expected)

        result = float_validation(val=expected, cast=True)
        self.assertEqual(float(expected), result)

    def test_float_validation_convert_fail_test(self):
        expected = 'appel'
        with self.assertRaises(Invalid):
            _ = float_validation(val=expected)

        with self.assertRaises(Invalid):
            _ = float_validation(val=expected, cast=True)

    def test_list_validation_invalid_val_test(self):
        non_list_types = ['str', 2, {}, tuple(), float()]
        for item in non_list_types:
            with self.assertRaises(Invalid):
                _ = list_validation(val=item)

    def test_list_validation_invalid_too_long_test(self):
        too_long = [1, 2, 3, 4, 5]
        with self.assertRaises(Invalid):
            _ = list_validation(val=too_long, max_amount=4)

    def test_list_validation_invalid_too_short_test(self):
        too_short = [1, 2, 3, 4, 5]
        with self.assertRaises(Invalid):
            _ = list_validation(val=too_short, min_amount=6)

    def test_dict_validation_invalid_val_test(self):
        non_dict_types = ['str', 2, [], tuple(), float()]
        for item in non_dict_types:
            with self.assertRaises(Invalid):
                _ = dict_validation(val=item)

    def test_dict_validation_invalid_too_long_test(self):
        too_long = {i: i for i in range(5)}
        with self.assertRaises(Invalid):
            _ = dict_validation(val=too_long, max_amount=4)

    def test_dict_validation_invalid_too_short_test(self):
        too_short = {i: i for i in range(5)}
        with self.assertRaises(Invalid):
            _ = dict_validation(val=too_short, min_amount=6)

    def test_dict_validation_valid_regex_test(self):
        dict_with_valid_keys = {str(i): i for i in range(5)}
        result = dict_validation(val=dict_with_valid_keys, key_regex='[0-9]')
        difference = ddiff(dict_with_valid_keys, result)
        self.assertEqual(difference, {})

    def test_dict_validation_invalid_regex_test(self):
        dict_with_invalid_keys = {str(i): i for i in range(5)}
        dict_with_invalid_keys['a'] = 'not valid'
        with self.assertRaises(Invalid):
            _ = dict_validation(val=dict_with_invalid_keys, key_regex='[0-9]')

    def test_dict_validation_invalid_types_regex_test(self):
        dict_with_invalid_keys = {
            'keys': None,
            None: None,
            1: None,
        }
        with self.assertRaises(Invalid):
            _ = dict_validation(val=dict_with_invalid_keys, key_regex='[0-9]')

    def test_uuid_validation_valid_uuids(self):
        for _ in range(10):
            expected = str(uuid.uuid4())
            result = uuid_validation(val=expected)
            self.assertEqual(expected, result)

    def test_uuid_validation_invalid_uuids(self):
        none_uuids = [
            str(uuid.uuid4()) + 'a',
            'appels',
            '92ue92ueof-03i903ir039-034i309',
            None,
            [],
            {},
        ]
        for item in none_uuids:
            with self.assertRaises(Invalid):
                _ = uuid_validation(val=item)

class ValidatorWrongInputTests(unittest.TestCase):
    def setUp(self):
        self.test_input = {
            'id': 23,
            'name': 'John Doe',
            'type': 'banana',
        }
        self.test_validation = {
            'id': {'validator': 'int', 'args': {'min_amount': 1}},
            'name': {'validator': 'str', 'args': {'min_length': 1, 'max_length': 35, 'regex': r'(\w+ )(\w+)'}},
            'type': {'validator': 'str', 'args': {'choices': ['apple', 'banana', 'citrus']}}
        }

    def test_missing_key_validation(self):
        """Items that are not expected are removed"""
        del self.test_validation['name']

        validated_items = maat_scale(self.test_input, self.test_validation)
        difference = ddiff(self.test_input, validated_items)
        self.assertEqual({'dictionary_item_removed': set(["root['name']"])}, difference)

    def test_not_set_validator(self):
        """Approriate message shown when trying to use a validator that is not registered"""
        test_input = {'id': 23}
        test_validation = {'id': {'validator': 'integer'}}

        with self.assertRaisesRegexp(Invalid, 'integer is not registered as validator'):
            _ = maat_scale(test_input, test_validation)

    def test_pre_post_transformation(self):
        """Input dict has item with type float, transform to int, validate as int, tranform back to int"""
        test_input = {'id': float(23)}
        test_validation = {'id': {'validator': 'int', 'transform': 'float', 'pre_transform': 'int'}}
        validated_items = maat_scale(test_input, test_validation)
        difference = ddiff(validated_items, test_input)
        self.assertEqual(difference, {})

    def test_not_set_pre_transformation_function(self):
        """Approriate message shown when trying to use pre transformation that is not registered"""
        test_input = {'id': float(23)}
        test_validation = {'id': {'validator': 'int', 'pre_transform': 'integer'}}
        with self.assertRaisesRegexp(Invalid, 'integer is not registered as transformation'):
            _ = maat_scale(test_input, test_validation)

    def test_not_set_post_transformation_function(self):
        """a helpfull message is shown when trying to use post transformation that is not registered"""
        test_input = {'id': 23}
        test_validation = {'id': {'validator': 'float', 'transform': 'integer'}}
        with self.assertRaisesRegexp(Invalid, 'integer is not registered as transformation'):
            _ = maat_scale(test_input, test_validation)

    def test_non_dictionary_function(self):
        """a helpfull message is shown when trying to use post transformation that is not registered"""
        test_input_list = ['id', float(23)]
        test_input_tuple = ('id', float(23))
        test_validation = {'id': {'validator': 'int', 'transform': 'int'}}
        with self.assertRaisesRegexp(Invalid, "\['id', 23.0\] not a dictionary but is of type <type 'list'>"):
            _ = maat_scale(test_input_list, test_validation)

        with self.assertRaisesRegexp(Invalid, "\('id', 23.0\) not a dictionary but is of type <type 'tuple'>"):
            _ = maat_scale(test_input_tuple, test_validation)

    def test_item_nullable(self):
        """a helpfull message is shown when trying to use post transformation that is not registered"""
        test_input = {'id': None}
        test_validation = {'id': {'validator': 'float'}}
        with self.assertRaisesRegexp(Invalid, 'id contains invalid item None: not of type float'):
            _ = maat_scale(test_input, test_validation)

        test_validation = {'id': {'validator': 'float', 'null_able': True}}
        validated_items = maat_scale(test_input, test_validation)
        difference = ddiff(validated_items, test_input)
        self.assertEqual(difference, {})

    def test_validate_skip_instead_of_fail_within_nested_list_with_custom_validation(self):
        from validation import registered_functions
        def blacklist_address(key, val):
            """Since this is a example blacklisted is hardcoded.
            It could come from config or an key value store at runtime
            Either within this function or given as argument.
            """
            blacklist = ['blacklisted', 'black_listed', 'BLACKLISTED']
            if val in blacklist:
                raise Invalid('{0} is in blacklist of {1}'.format(key, val))
            return val

        registered_functions['valid_address'] = blacklist_address
        test_input = {
            'id': 23,
            'addresses': [
                'blacklisted',
                'valid adress',
                'also valid address',
                'black_listed',
                'valid again',
                'BLACKLISTED',
            ]
        }
        test_validation = {
            'id': {'validator': 'int', 'args': {'min_amount': 1}},
            'addresses': {'validator': 'valid_address', 'skip_failed': True, 'list': True, 'nested': True}
        }
        expected_result = {
            'id': 23,
            'addresses': [
                'valid adress',
                'also valid address',
                'valid again',
            ]
        }
        validated_items = maat_scale(test_input, test_validation)
        difference = ddiff(validated_items, expected_result)
        self.assertEqual(difference, {})

    def test_validate_fail_within_nested_list_with_custom_validation(self):
        from validation import registered_functions
        def blacklist_address(key, val):
            """Since this is a example blacklisted is hardcoded.
            It could come from config or an key value store at runtime
            Either within this function or given as argument.
            """
            blacklist = ['blacklisted', 'black_listed', 'BLACKLISTED']
            if val in blacklist:
                raise Invalid('{0} is in blacklist of {1}'.format(key, val))
            return val

        registered_functions['valid_address'] = blacklist_address
        test_input = {
            'id': 23,
            'addresses': [
                'valid adress',
                'blacklisted',
            ]
        }
        test_validation = {
            'id': {'validator': 'int', 'args': {'min_amount': 1}},
            'addresses': {'validator': 'valid_address', 'list': True, 'nested': True}
        }
        with self.assertRaisesRegexp(Invalid, "addresses is in blacklist of blacklisted"):
            _ = maat_scale(test_input, test_validation)

    def test_validate_fail_within_nested_list_dicts_with_custom_validation(self):
        from validation import registered_functions
        def blacklist_address(key, val):
            """Since this is a example blacklisted is hardcoded.
            It could come from config or an key value store at runtime
            Either within this function or given as argument.
            """
            blacklist = ['blacklisted', 'black_listed', 'BLACKLISTED']
            if val in blacklist:
                raise Invalid('{0} is in blacklist of {1}'.format(key, val))
            return val

        registered_functions['valid_address'] = blacklist_address
        test_input = {
            'id': 23,
            'addresses': [
                {'street': 'valid adress'},
                {'street': 'blacklisted'},
            ]
        }
        test_validation = {
            'id': {'validator': 'int', 'args': {'min_amount': 1}},
            'addresses': {'validator': 'list', 'list_dicts': True, 'nested': {
              'street': {'validator': 'valid_address'}}
            }
        }
        with self.assertRaisesRegexp(Invalid, "street is in blacklist of blacklisted"):
            _ = maat_scale(test_input, test_validation)

class TestValidationDecorator(unittest.TestCase):

    def setUp(self):
        self.test_input = {
            'number': 23,
            'name': 'John Doe',
            'kind': 'banana',
        }
        self.test_validation = {
            'number': {'validator': 'int', 'args': {'min_amount': 1}},
            'name': {'validator': 'str', 'args': {'min_length': 1, 'max_length': 35, 'regex': r'(\w+ )(\w+)'}},
            'kind': {'validator': 'str', 'args': {'choices': ['apple', 'banana', 'citrus']}}
        }

    def test_validation_of_arguments(self):
        """Happy path test"""
        @validate_args(self.test_validation)
        def foo(number, name, kind):
            return locals()

        result = foo(**self.test_input)
        difference = ddiff(result, self.test_input)

        # if the differ finds no difference a empty dictionary is returned
        self.assertEqual(difference, {})

    def test_validation_of_argument_fail(self):
        """Test with validation failures"""

        @validate_args(self.test_validation)
        def foo(number, name, kind):
            return locals()

        # change type of number from int to str
        with self.assertRaisesRegexp(Invalid, 'number contains invalid item 2: not of type integer'):
            result = foo(number='2', name='foo bar', kind='apple')

        # let's remove an argument
        with self.assertRaisesRegexp(Invalid, 'kind: missing key'):
            result = foo(number=2, name='foo bar')

    def test_validation_of_argument_fail_returns_none(self):
        """Test with validation failures handle them and return None"""

        @validate_args(self.test_validation, fail_is_none=True)
        def foo(number, name, kind):
            return locals()

        # change type of number from int to str
        result = foo(number='2', name='foo bar', kind='apple')
        self.assertEqual(result, None)
        # let's remove an argument
        result = foo(number=2, name='foo bar')
        self.assertEqual(result, None)

    def test_validation_of_argument_fail_with_custom_exception(self):
        """Test with validation failures raises an custom exception"""

        @validate_args(self.test_validation, custom_exception=KeyError)
        def foo(number, name, kind):
            return locals()

        # change type of number from int to str
        with self.assertRaisesRegexp(KeyError, ''):
            result = foo(number='2', name='foo bar', kind='apple')

        # let's remove an argument
        with self.assertRaisesRegexp(KeyError, ''):
            result = foo(number=2, name='foo bar')


if __name__ == '__main__':
    unittest.main()