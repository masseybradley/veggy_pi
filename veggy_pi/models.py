from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


import bitarray
import json


from . funcs import is_number, all_numbers, is_greater_than, value_in_range, list_val_to_int, shift_bit_list


class VeggyConfiguration(models.Model):
    """
    this is the configuration class, config classes have comprehensible labels
    i.e. main_config and can have multiple config items with user defined values.
    """
    label = models.CharField(max_length=100)
    parent_config = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    user_config = models.ManyToManyField('ConfigurationOption', through='UserInput')
    def __unicode__(self):
        return self.label

    def get_values(self, config_list=[], values=[]):
        """
        recursively builds and returns a values_list with user input items.
        you shouldn't overwrite the default arguments - the config_list ensures
        that there is no infinite recursion and the values list is populated 
        and returned with the config.userinput_set.values() for each config.
        """
        config_list.append(self.pk)
        objs = self.userinput_set.values()
        
        for obj in objs:
            if obj in values:
                pass
            else:
                values.append(obj)

        # prevents infinite recursion by avoiding to re-enter a parent item
        # which has already been traversed
        if self.parent_config and self.parent_config.pk not in config_list:
            # passing the default values rather the lists passed to the first 
            # method call results in buggy behaviour - fixed
            self.parent_config.get_values(config_list, values)
            
        return values

    @staticmethod
    def get_unique_values(values, debug=False):
        """
        takes a values list and returns the list with the first occurrence of
        each variable_id - the order of the value_list will determine the parent / child
        configuratoin elements order.
        """
        if not values:
            raise ValueError(_('empty list'))

        if debug:
            print "\n input ------------------------------------------------------------"
            for val in values:
                print val
            print "-------------------------------------------------------------------"

        # save a list of unique ids
        variable_list = set(v[u'variable_id'] for v in values)

        for val in values:
            if val[u'variable_id'] in variable_list: 
                duplicates = [obj for obj in values if obj.get(u'variable_id') == val[u'variable_id'] and obj != val]
                for elem in duplicates:
                    values.remove(elem)

        if debug:
            print "\n output ------------------------------------------------------------"
            for val in values:
                print val
            print "--------------------------------------------------------------------"

        return values
    
    @staticmethod
    def validate_unique_values(values):
        """
        validate_unique_values does the relation between user input values
        and data types i.e. min_ph = float(), min_temp = int(), etc. and provides for custom 
        validation for user input i.e. if max_temp < min_temp: raise ValueError('min > max').

        this whole class is susceptible to be deprecated and replaced with built-in 
        Condition(s) and ConditionGroups instances.
        """
        if not values:
            raise ValueError(_(u'empty list'))
        
        for elem in values:
            option = ConfigurationOption.objects.get(pk=elem[u'variable_id'])
            if option.option_label == u'min_temp':
                min_temp = float(elem[u'value'])
            elif option.option_label == u'max_temp':
                max_temp = float(elem[u'value']) 
            elif option.option_label == u'max_ph':
                min_ph = float(elem[u'value'])
            elif option.option_label == u'min_ph':
                max_ph = float(elem[u'value'])
            elif option.option_label == u'min_ec':
                min_ec = float(elem[u'value'])
            elif option.option_label == u'min_rh':
                min_rh = int(elem[u'value'])
            elif option.option_label == u'max_rh':
                max_rh = int(elem[u'value'])
            elif option.option_label == u'temp_format':
                temp_format = elem[u'value']
                # temperature format field which will define which conversion
                # type should be used i.e. celcius -> farenheit and the max_range
                # for each.
                if elem[u'value'] == u'celcius':
                    temp_range = range(-273,100)
                elif elem[u'value'] == u'farenheit':
                    temp_range = range(-459, 212)
                elif elem[u'value'] == u'kelvin':
                    temp_range = range(0,373)
                else:
                    raise ValueError(_(u'acceptable values are: celcius, farenheit or kelvin'))

        # user input validation
        # temperatur
        if min_temp or max_temp:
            try:
                if not temp_range:
                    pass
            # variable would be unbound if temp input items end up
            # in a config without a temperature format type therefore no range.
            except UnboundLocalError:
                raise ValueError(_(u'temp_input elements require a temperature format type'))

            if min_temp:
                value_in_range(val=min_temp, max_range=temp_range)
                    
            if max_temp: 
                value_in_range(val=max_temp, max_range=temp_range)
        if min_temp and max_temp:
            is_greater_than(max_val=max_temp, min_val=min_temp)

        # ph 
        if min_ph or max_ph:
            ph_range = range(15)[1:]    
            if min_ph:
                value_in_range(val=min_ph, max_range=ph_range)
            if max_ph:
                value_in_range(val=max_ph, max_range=ph_range)
        if min_ph and max_ph:
            is_greater_than(max_val=max_ph, min_val=min_ph)

        # ec
        if min_ec and max_ec:
            is_greater_than(max_val=max_ec, min_val=min_ec)
        
        # relative humidity
        if min_rh or max_rh:
            rh_range = range(0,100)
            if min_rh:
                value_in_range(val=min_rh, max_range=rh_range)
            if max_rh:
                value_in_range(val=max_rh, max_range=rh_range)
        if min_rh and max_rh:
            is_greater_than(max_val=max_rh, min_val=min_rh) 


class UserInput(models.Model):
    """
    this is where user input is stored for configuration options.
    """
    veggy_config = models.ForeignKey('VeggyConfiguration')
    variable = models.ForeignKey('ConfigurationOption')
    value = models.CharField(max_length=10)
    class Meta:
        unique_together = ('veggy_config', 'variable')
    def __unicode__(self):
        return "%s - %s: %s" % (self.veggy_config.label, self.variable, self.value)


class ConfigurationOption(models.Model):
    """
    configuration options with a comprehensive label i.e. max_temp, 
    max_ph, etc. and optionally a parent_option for classification
    """
    parent_option = models.ForeignKey('ConfigurationOption', null=True, on_delete=models.SET_NULL)
    option_label = models.CharField(max_length=30, unique=True)
    def __unicode__(self):
        return self.option_label


class VeggyModel(models.Model):
    """
    this is the shared base class for our models, it just provides
    some common fields and a "state"
    """
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        abstract = True


class Input(VeggyModel):
    """
    Everything that was read in by all of the sensors
    """
    # content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    # object_id = models.PositiveIntegerField()
    # content_object = GenericForeignKey('content_type', 'object_id')
    sensor_name = models.TextField()
    value = models.TextField()


class Reading(VeggyModel):
    sensor = models.ForeignKey("Sensor", null=False)
    data = models.TextField()

    def save(self, *args, **kwargs):
        """
        when a Reading is saved it updates the current_reading
        of the related sensor to `self`.
        """
        super(Reading, self).save(*args, **kwargs)
        self.sensor.current_reading = self
        self.sensor.save()
    def __unicode__(self):
        return "%s: %s - %s" % (self.created_at, self.sensor.name, self.data)


class Pin(models.Model):
    """
    pin mappings class - built and tested on RPi (fixtures available) but generic 
    enough to accomodate for any i/o device.
    """
    pin_number = models.SmallIntegerField(null=False, blank=False, editable=False)
    # i.e. io_1, io_2, out_5v, ground
    # to think about: maybe add a current_state here being either input or output saved
    # with a fk to reading in order to have a tracking of when a pin changed from input to output
    # or set low to high
    label = models.CharField(max_length=10, null=False, blank=False, editable=False)
    def __unicode__(self):
        return "%s: %s" % (self.pin_number, self.label)


class RPiPin(Pin):
    """
    rasperry pi pin mappings and controller - fixtures for 40 pin pi model b+ / pi 2 model b
    """
    class Meta:
        proxy = True

    def setup(self):
        try:
            import RPi.GPIO as GPIO
            global GPIO
            print "GPIO ready."
            # should be replaced later on with a user config option i.e. GPIO_MODE
            GPIO.setmode(GPIO.BOARD)
        except Exception as ex:
            raise ex
        
    def set_mode(self, mode):
        # pin mode - valid modes are either input or output
        io_pins = (3, 5, 7, 8, 10, 11, 12, 13, 15, 16, 18, 19, 21, 22, 23, 24, 26, 27, 28, 29, 31, 32, 33, 35, 36, 37, 38, 40)

        # where mode is either input or output 
        if not mode:
            raise ValueError(u'no mode provided.')

        if self.pin_number not in io_pins:
            raise ValueError(u'can not set a non io pin mode.')

        # need sudo privileges to set the pin mode
        if mode == u'input':
            GPIO.setup(self.pin_number, GPIO.IN)
        elif mode == u'output':
            GPIO.setup(self.pin_number, GPIO.OUT)
        else:
            raise ValueError(u'valid modes are input or output.')
        
    def set_output(self, out=False):
        # true = HIGH
        # flase = LOW
        if out:
            GPIO.output(self.pin_number, GPIO.HIGH)
        else:
            GPIO.output(self.pin_number, GPIO.LOW)


class Sensor(models.Model):
    """
    generic sensor class - this class is proxied with actual physical sensors which define
    their own read method for each physical sensor. 
    """
    name = models.TextField(null=False, blank=False)
    current_reading = models.ForeignKey("Reading", null=True, default=None, related_name="latest_sensor")
    pin = models.ForeignKey("Pin", null=True)

    def plug_into(self, pin_numbers):
        self.unplug() # remove any existing connection first
        for pin_number in pin_numbers:
            Pin.objects.create(number=pin_number, sensor=self)

    def unplug(self):
        for pin in self.pin_set.all():
            pin.delete()

    def read(self):
        raise NotImplemented()


class DHT22Sensor(Sensor):
    class Meta:
        proxy = True

    def read(self):
        # returns 40 bits i.e. 0000 0010 1000 1100  0000 0001 0101 1111  1110 1110
        #                      relative humidity    temperature          checksum
        pass


class Thermometer(Sensor):
    class Meta:
        proxy = True
    def read(self):
        my_pin_numbers = [pin.number for pin in self.pin_set.all()]
        # ...


class Operator(object):
    """
    An Eumm of operators used in the evaluating conditions
    and condition groups.
    """
    # logic:
    AND = 1
    OR = 2
    XOR = 3
    # compare:
    EQUALS = 4
    NOT_EQUALS = 5
    # >, <, >=, <=
    GT = 6
    LT = 7
    GTE = 8
    LTE = 9
    

class SensorState(dict):
    """
    this is an extended dict which catches call to key lookups ( my_dict['xxx'] )
    and can delegate them to do "calculated values".
    """
    def __init__(self, *args, **kwargs):
        if 'senors' in kwargs:
            self._sensors = kwargs.pop('sensors')
        else:
            self._sensors = {}
        super(SensorState, self).__init__(*args, **kwargs)

    def __getitem__(self, key):
        try:
            func = self._sensors[key]
            return func()
        except KeyError:
            return super(SensorState, self).__getitem__(key)


class ConditionGroup(VeggyModel):
    """
    Groups together multiple conditions with logic operators
    """
    operator = models.PositiveIntegerField(default=Operator.AND, choices=(
        (Operator.AND, 'AND'),
        (Operator.OR, 'OR'),
    ))

    def evaluate(self, sensor_state):
        """
        evaluates each of the children Conditions usings the logic operator
        of self to determine the groups overall value.
        expects a dict (like) sensor_state (see SensorState)
        """
        if self.operator == Operator.AND:
            for c in self.condition_set.all():
                if not c.evaluate(sensor_state):
                    return False
            return True

        if self.operator == Operator.OR:
            for c in self.condition_set.all():
                if c.evaluate(sensor_state):
                    return True
            return False

        raise NotImplemented("missing operator: %s" % (self.operator))


class Condition(VeggyModel):
    """
    represents a logic condition comparing the left hand side to the right
    (lhs, rhs) using a compare operator.
    """
    group = models.ForeignKey("ConditionGroup", null=True, default=None)
    lhs = models.TextField(null=False, blank=True, default=None)
    rhs = models.TextField(null=False, blank=True, default=None)
    operator = models.PositiveIntegerField(default=Operator.EQUALS, choices=(
        (Operator.EQUALS, '=='),
        (Operator.NOT_EQUALS, '!='),
        (Operator.GT, '>'),
        (Operator.LT, '<'),
        (Operator.GTE, '>='),
        (Operator.LTE, '<='),
    ))

    def evaluate(self, sensor_state):
        """
        expects a dict (like) sensor_state (see SensorState)
        """
        lhs_val = sensor_state[self.lhs]
        rhs_val = self.rhs

        if all_numbers(lhs_val, rhs_val):
            lhs_val = float(lhs_val)
            rhs_val = float(rhs_val)

        _funcs = {
            Operator.EQUALS: lambda l,r: l == r,
            Operator.NOT_EQUALS: lambda l,r: l != r,
            Operator.GT: lambda l,r: l > r,
            Operator.LT: lambda l,r: l < r,
            Operator.GTE: lambda l,r: l >= r,
            Operator.LTE: lambda l,r: l <= r,
        }

        func = _funcs[self.operator]

        return func(lhs_val, rhs_val)

    def __unicode__(self):
        return u"%s [[operator code %s]] %s" % (self.lhs, self.operator, self.rhs)
