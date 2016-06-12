from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from . funcs import is_number, all_numbers


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
    def get_unique_values(values):
        """
        takes a values list and returns the list with the first occurrence of
        each variable_id - the order of the value_list will determine the parent / child
        configuratoin elements order.
        """
        if not values:
            raise ValueError('empty list')

        # debug
        print "\n input ------------------------------------------------------------"
        for val in values:
            print val
        print "-------------------------------------------------------------------"

        # save a list of unique ids
        variable_list = []
        for val in values:
            if val[u'variable_id'] in variable_list:
                pass
            else:
                variable_list.append(val[u'variable_id'])

        for val in values:
            # print "got val: ", val
            if val[u'variable_id'] in variable_list: 
                duplicates = [obj for obj in values if obj.get(u'variable_id') == val[u'variable_id'] and obj != val]
                for elem in duplicates:
                    # print "removing element: ", elem
                    values.remove(elem)

        # debug
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

        config values should always be validated i.e.
        config.validate_unique_values(config.get_unique_values(sorted(config.get_values(), key=...)))
        """
        if not values:
            raise ValueError(u'empty list')

        max_temp = int()
        min_temp = int()

        max_ph = float()
        min_ph = float()

        for elem in values:
            option = ConfigurationOption.objects.get(pk=elem[u'variable_id'])
            if option.option_label == u'max_temp':
                max_temp = int(elem[u'value']) 
            elif option.option_label == u'min_temp':
                min_temp = int(elem[u'value'])
            elif option.option_label == u'max_ph':
                min_ph = float(elem[u'value'])
            elif option.option_label == u'min_ph':
                max_ph = float(elem[u'value'])

        if min_temp and max_temp:
            validate_greater_than(max_temp, min_temp)
        
        if min_ph or max_ph:
            ph_range = range(15)[1:]    
            if min_ph:
                validate_value_in_range(min_ph, ph_range)
            if max_ph:
                validate_value_in_range(max_ph, ph_range)

        if min_ph and max_ph:
            validate_greater_than(max_ph, min_ph)


# static validation methods
def validate_greater_than(max_val, min_val):
    if min_val > max_val or min_val == max_val:
        raise ValueError('%s must not be greater than %s' % (min_val, max_val))   
        
def validate_value_in_range(val, max_range):
    if val not in max_range:
        raise ValueError('%s must be in range %s' % (val, max_range))

class UserInput(models.Model):
    """
    this is where user input is stored for configuration options
    """
    veggy_config = models.ForeignKey('VeggyConfiguration', on_delete=models.CASCADE)
    variable = models.ForeignKey('ConfigurationOption')
    value = models.CharField(max_length=10)
    class Meta:
        unique_together = ('veggy_config', 'variable')
    def __unicode__(self):
        return "%s - %s: %s" % (self.veggy_config.label, self.variable, self.value)


class ConfigurationOption(models.Model):
    """
    configuration options with a comprehensive lable i.e. max_temp, 
    max_ph, etc. and optionally a parent_option for classification
    """
    # options can be classified with parent options i.e.:
    # option = ConfigurationOption(option_label="temperature")
    # max_temp = ConfigurationOption(option_label="max_temp", parent_option=option)
    # min_temp = ConfigurationOption(option_label="min_temp", parent_option=option)
    parent_option = models.ForeignKey('ConfigurationOption', null=True, on_delete=models.SET_NULL)
    option_label = models.CharField(max_length=30)
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


class Reading(models.Model):
    sensor = models.ForeignKey("Sensor", null=False)

    def save(self, *args, **kwargs):
        """
        when a Reading is saved it updates the current_reading
        of the related sensor to `self`.
        """
        super(Reading, self).save(*args, **kwargs)
        self.sensor.current_reading = self
        self.sensor.save()


class RPiPin(models.Model):
    """
    raspberry pi pin mappings.
    """
    number = models.SmallIntegerField(null=False, blank=False, editable=False)
    # i.e. io_1, io_2, out_5v, ground
    label = models.CharField(max_length=10)
    sensor = models.ForeignKey("Sensor", null=False)


class Sensor(models.Model):
    name = models.TextField(null=False, blank=False)
    current_reading = models.ForeignKey("Reading", null=True, default=None, related_name="latest_sensor")

    def plug_into(self, pin_numbers):
        self.unplug() # remove any existing connection first
        for pin_number in pin_numbers:
            Pin.objects.create(number=pin_number, sensor=self)

    def unplug(self):
        for pin in self.pin_set.all():
            pin.delete()

    def read(self):
        raise NotImplemented()


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
