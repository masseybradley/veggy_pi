from django.test import TestCase

from . funcs import (
    is_number,
    all_numbers,
    )

from . models import (
    Condition,
    ConditionGroup,
    Operator,
    SensorState,
    VeggyConfiguration,
    ConfigurationOption,
    UserInput,
    Pin,
    DHT22Sensor,
    )

from www.settings import TIME_ZONE


from datetime import datetime
import pytz


class TestPureFunctions(TestCase):
    def test_is_number(self):
        self.assertTrue(is_number(42))
        self.assertTrue(is_number(1.2))
        self.assertTrue(is_number("-5393"))
        self.assertTrue(is_number("123.9"))

    def test_not_numbers(self):
        self.assertFalse(is_number("hello"))
        self.assertFalse(is_number("0x80"))

    def test_all_numbers(self):
        self.assertTrue(all_numbers(1,2,3))
        self.assertTrue(all_numbers(3.14))
        self.assertTrue(all_numbers("2", "1"))
        self.assertTrue(all_numbers("3.243", 7))
        self.assertTrue(all_numbers(7, "7", "8", "2.44", 2.1, -1, "-123"))

    def test_not_all_numbers(self):
        self.assertFalse(all_numbers("hacker"))
        self.assertFalse(all_numbers(1,2,3,"four"))


class TestCondition(TestCase):
    def test_equals(self):
        c1 = Condition(lhs='SENSOR_1', rhs=13, operator=Operator.EQUALS)
        c2 = Condition(lhs='SENSOR_2', rhs='hacker', operator=Operator.EQUALS)

        self.assertTrue(c1.evaluate(SensorState(SENSOR_1=13)))
        self.assertFalse(c1.evaluate(SensorState(SENSOR_1=12)))
        self.assertTrue(c2.evaluate(SensorState(SENSOR_2='hacker')))
        self.assertFalse(c2.evaluate(SensorState(SENSOR_2='script kiddie')))

    def test_not_equals(self):
        c1 = Condition(lhs='SENSOR_1', rhs=13, operator=Operator.NOT_EQUALS)
        c2 = Condition(lhs='SENSOR_2', rhs='hacker', operator=Operator.NOT_EQUALS)

        self.assertTrue(c1.evaluate(SensorState(SENSOR_1='12')))
        self.assertFalse(c1.evaluate(SensorState(SENSOR_1='13')))
        self.assertTrue(c2.evaluate(SensorState(SENSOR_2='jack daniels')))


class TestConditionGroup(TestCase):
    def setUp(self):
        self.g1 = ConditionGroup(operator=Operator.AND)
        self.g2 = ConditionGroup(operator=Operator.OR)
        self.g1.save()
        self.g2.save()

    def test_and(self):
        c1 = Condition(lhs='SENSOR_1', operator=Operator.LT, rhs=32.5, group=self.g1)
        c2 = Condition(lhs='SENSOR_1', operator=Operator.GT, rhs=28.0, group=self.g1)
        c1.save()
        c2.save()

        self.assertTrue(self.g1.evaluate({'SENSOR_1': 30}))
        self.assertFalse(self.g1.evaluate({'SENSOR_1': 40}))
        self.assertFalse(self.g1.evaluate({'SENSOR_1': 20}))
    
    def test_or(self):
        c1 = Condition(lhs='X', operator=Operator.EQUALS, rhs=42, group=self.g2)
        c2 = Condition(lhs='X', operator=Operator.LT, rhs='0', group=self.g2)
        c1.save()
        c2.save()

        self.assertTrue(self.g2.evaluate(SensorState(X=42)))
        self.assertTrue(self.g2.evaluate(SensorState(X="-100")))
        self.assertFalse(self.g2.evaluate(SensorState(X=0)))
        self.assertFalse(self.g2.evaluate(SensorState(X=13)))


class TestVeggyConfiguration(TestCase):
    def setUp(self):
        # start_time = datetime(0000, 00, 00, 12, 00, 00, 0, pytz.UTC)
        # end_time = datetime(0000, 00, 00, 18, 00, 00, 0, pytz.UTC)

        self.main_config = VeggyConfiguration(label=u'main_config')
        self.main_config.save()

        self.day_config = VeggyConfiguration(label=u'day_config', parent_config=self.main_config)
        self.night_config = VeggyConfiguration(label=u'night_config', parent_config=self.main_config)
        self.override_config = VeggyConfiguration(label=u'override_config', parent_config=self.day_config)
        self.temp_config = VeggyConfiguration(label=u'temp_config', parent_config=self.override_config)

        self.day_config.save()
        self.night_config.save()
        self.override_config.save()
        self.temp_config.save()
            
        self.temp_option = ConfigurationOption(option_label=u'temperature')
        self.humidity_option = ConfigurationOption(option_label=u'humidity')
        self.temp_option.save()
        self.humidity_option.save()

        self.temp_format = ConfigurationOption(option_label=u'temp_format', parent_option=self.temp_option)
        self.temp_format.save()

        self.max_temp = ConfigurationOption(option_label=u'max_temp', parent_option=self.temp_option)
        self.min_temp = ConfigurationOption(option_label=u'min_temp', parent_option=self.temp_option)
        self.min_temp.save()
        self.max_temp.save()

        self.max_rh = ConfigurationOption(option_label=u'max_rh', parent_option=self.humidity_option)
        self.min_rh = ConfigurationOption(option_label=u'min_rh', parent_option=self.humidity_option)
        self.max_rh.save()
        self.min_rh.save()

        self.min_ph = ConfigurationOption(option_label=u'min_ph')
        self.max_ph = ConfigurationOption(option_label=u'max_ph')
        self.min_ph.save()
        self.max_ph.save()

        self.user_temp_format = UserInput(veggy_config=self.main_config, variable=self.temp_format, value=u'celcius')
        self.user_temp_format.save()

        self.user_min_ph = UserInput(veggy_config=self.main_config, variable=self.min_ph, value=u'5.5')
        self.user_max_ph = UserInput(veggy_config=self.main_config, variable=self.max_ph, value=u'12')
        self.user_min_ph.save()
        self.user_max_ph.save()

        self.user_min_temp_day = UserInput(veggy_config=self.day_config, variable=self.min_temp, value=u'26')
        self.user_max_temp_day = UserInput(veggy_config=self.day_config, variable=self.max_temp, value=u'28')
        
        self.user_min_temp_day.save()
        self.user_max_temp_day.save()
        
        self.override_temp = UserInput(veggy_config=self.override_config, variable=self.max_temp, value=u'10')
        self.override_temp.save()

        self.ph_range = range(15)[1:]
        self.user_min_ph = UserInput(veggy_config=self.temp_config, variable=self.min_ph, value=u'15')
        self.user_max_temp = UserInput(veggy_config=self.temp_config, variable=self.max_temp, value=u'30')
        self.user_min_ph.save()
        self.user_max_temp.save()
    
        self.values = []
        self.config_list = []
        self.main_config_items = self.main_config.get_values(self.config_list, self.values)

        self.values = []
        self.config_list = []
        self.day_config_items = self.day_config.get_values(self.config_list, self.values)

        self.values = []
        self.config_list = []
        self.override_config_items = self.override_config.get_values(self.config_list, self.values)

        self.values = []
        self.config_list = []
        self.temp_config_items = self.temp_config.get_values(self.config_list, self.values)

        self.values = []
        self.config_list = []
        self.night_config_items = self.night_config.get_values(self.config_list, self.values)
        
    def test_get_values(self):
        # verify that the values_list returned by a configuration instance
        # contains all configuration items linked to that instance as well as
        # parent instance items
        self.assertTrue(len(self.main_config_items) == 3)
        self.assertTrue(len(self.day_config_items) == 5)
        self.assertTrue(len(self.override_config_items) == 6)
        self.assertTrue(len(self.temp_config_items) == 8)
        # night config does not define any variables but still
        # inherits the main_config (parent) items
        self.assertTrue(len(self.night_config_items) == 3)
    
    def test_infinite_recursion_protection(self):
        # parent config has a child config which has a pointer back to the
        # parent config instance creating an infinte loop retreiving the config
        # items - the config_list prevents this by keeping track of which config
        # instances have already been traversed and if such circumstances were to 
        # ever occur you end up with the same values_list no matter from which config 
        # you get_values from
        self.main_config.parent_config = self.day_config
        self.main_config.save()
        
        self.values = []
        self.config_list=[]
        values = self.day_config.get_values(self.config_list, self.values)
        for obj in self.day_config.userinput_set.values():
            self.assertTrue(obj in values)
        for obj in self.main_config.userinput_set.values():
            self.assertTrue(obj in values)
        
        self.values = []
        self.config_list=[]
        self.main_config.get_values(self.config_list, self.values)
        for obj in self.day_config.userinput_set.values():
            self.assertTrue(obj in values)
        for obj in self.main_config.userinput_set.values():
            self.assertTrue(obj in values)

        self.main_config.parent_config = None
        self.main_config.save()
    
    def test_get_unique_values(self):
        # the nature of the recursive function will always return a list
        # grouped by veggy_config_id
        self.config_list = []
        self.values = []
        values = self.override_config.get_unique_values(self.override_config.get_values(self.config_list, self.values))
        # for val in values:
        #     if val[u'id'] == self.override_temp.pk:
        #         print "override value: ", val

        for obj in self.main_config.userinput_set.values():
            self.assertTrue(obj in values)
        for obj in self.day_config.userinput_set.values():
            if obj[u'variable_id'] == self.max_temp.pk:
                self.assertTrue(obj not in values) 
        for obj in self.override_config.userinput_set.values():
            if obj[u'variable_id'] == self.max_temp.pk:
                self.assertTrue(obj in values)
        # make sure temp_config items are not in the result_set
        for obj in self.temp_config.userinput_set.values():
            if obj[u'variable_id'] == self.user_max_temp.pk:
                self.assertTrue(obj not in values)            
   
        # reversing the values_list results in the inverse - parent items take 
        # precedence over any duplicate child configuration items
        self.config_list = []
        self.values = []
        values = self.override_config.get_unique_values(self.override_config.get_values(self.config_list, self.values)[::-1])
        for obj in self.main_config.userinput_set.values():
            self.assertTrue(obj in values)
        for obj in self.day_config.userinput_set.values():
            if obj[u'variable_id'] == self.max_temp.pk:
                self.assertTrue(obj in values) 
        for obj in self.override_config.userinput_set.values():
            if obj[u'variable_id'] == self.max_temp.pk:
                self.assertTrue(obj not in values)

    def test_empty_unique_values_value_error(self):
        """
        an attempt to sort an empty list of values will raise a value error
        """
        values = []
        with self.assertRaises(ValueError) as ex:
            self.main_config.get_unique_values(values)
        
        exception = ex.exception
        self.assertEquals(exception.args, (u'empty list',))

    def test_values_greater_than_validation(self):
        """
        max_val greater than min_val static method test.
        """
        self.config_list = []
        self.values = []
        with self.assertRaises(ValueError) as ex:
            self.override_config.validate_unique_values(self.override_config.get_unique_values(self.override_config.get_values(self.config_list, self.values), debug=True))
        
        exception = ex.exception
        self.assertEquals(exception.args, (u'%s must not be greater than %s' % (float(self.user_min_temp_day.value), float(self.override_temp.value)),))
    
    def test_values_in_range_validation(self):
        self.config_list = []
        self.values = []
        values = self.temp_config.get_values(self.config_list, self.values)

        with self.assertRaises(ValueError) as ex:
            self.temp_config.validate_unique_values(self.temp_config.get_unique_values(self.temp_config.get_values(self.config_list, self.values), debug=True))
        
        exception = ex.exception
        self.assertEquals(exception.args, (u'%s must be in range %s' % (float(self.user_min_ph.value), self.ph_range),))
    
    def test_temp_input_with_invalid_format(self):
        self.user_temp_format.value = u'inexistant'
        self.user_temp_format.save()

        self.config_list = []
        self.values = []
        values = self.main_config.get_values(self.config_list, self.values)

        with self.assertRaises(ValueError) as ex:
            self.temp_config.validate_unique_values(self.temp_config.get_unique_values(self.temp_config.get_values(self.config_list, self.values), debug=True))
        
        exception = ex.exception
        self.assertEquals(exception.args, (u'acceptable values are: celcius, farenheit or kelvin',))
    
    def test_temp_input_with_no_format(self):
        """
        temp input values without a format with raise an exception
        """
        self.user_temp_format.delete()

        self.config_list = []
        self.values = []
        values = self.main_config.get_values(self.config_list, self.values)

        with self.assertRaises(ValueError) as ex:
            self.temp_config.validate_unique_values(self.temp_config.get_unique_values(self.temp_config.get_values(self.config_list, self.values), debug=True))
        
        exception = ex.exception
        print exception.args
        self.assertEquals(exception.args, ('temp_input elements require a temperature format type',))
 

    def tearDown(self):
        VeggyConfiguration.objects.all().delete()
        UserInput.objects.all().delete()
        ConfigurationOption.objects.all().delete()
