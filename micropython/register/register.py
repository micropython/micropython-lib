"""
    * Author(s): SquirtleSquadLeader
    
    * License: MIT
        
    * Purpose:
        * The purpose of this module is to provide easy I2C Register
        * access.  It is inspired by the CircuitPython Register
        * module maintained by Adafruit.
        
            * RORegBit - Single bit Read Only 
            * RWRegBit - Single bit Read/Write
            
            * RORegBits - Multi-bit Read Only
            * RWRegBits - Multi-bit Read/Write
            
            * ROReg - Single/Multi Read Only
            * RWReg - Single/Multi Read/Write
            
        
    * Notes:
        1) Reference format strings below:                   
             Format          C Type          Standard size    
                c         char                    1
                b         signed char             1
                B         unsigned char           1
                h         short                   2
                H         unsigned short          2
                i         integer                 4
                I         unsigned int            4
                l         long                    4
                L         unsigned long           4
                q         long long               8
                Q         unsigned long long      8
                f         float                   4
                d         double                  8
   

"""

from machine import I2C
from struct import pack, unpack

class RORegBit:
    def __init__(self, i2c, dev_addr, reg_addr, num_bytes, bit_location, endian='', fmt='B'):
        """
        Creates an :class:`RORegBit` object which allows read only access to a single bit within a register. 
            
            
        :param i2c: I2C bus which connects the host system to the peripheral device
        :type kind: machine.I2C()
        :param dev_addr: I2C address of the device which  
        :type dev_addr: int() 
        :param reg_addr: Physical register address which contains the bit of interest  
        :type reg_addr: int() 
        :param num_bytes: Number of bytes to read  
        :type num_bytes: int() 
        :param bit_location: Location of bit within bitfield  
        :type bit_locatin: int() 
        :param endian: Endian-ness of system for which the code is intended to run on. str('') uses native Endian-ness.   
        :type endian: str()
        :param fmt: Format code which is used to unpack data from bytes().  Defaults to 'B' which is good for a single 8-bit register  
        :type fmt: int() 
        
        :return: An initialized RORegBit object
        :rtype: RORegBit()
        
        
         **Quickstart: Importing and using the device**

        Here is an example of using the :class:`RORegBit` class.  
        First you will need to import the following libraries:

        .. code-block:: python
        
            from machine import I2C
            from register.register import RORegBit

        Once this is done you must define a :class:`machine.I2C` object and then pass that
        to the :class:`RORegBit` object to instantiate it.
                
        .. code-block:: python

            i2c = I2C(0)  # I2C details are project specific
            
            my_reg = RORegBit(i2c, 68, 5, 1, 5)
            
        'my_reg' can now provide access to the :method:`__get__().  Using this method
        will return the value of the bit found at :param bit_location:.       

        .. code-block:: python
            
            value = my_reg.__get__() # 0 or 1
        
        Alternatively, a :class:`RORegBit` object(s) can be placed within another class.

        .. code-block:: python
            # import 
            from machine import I2C
            from register.register import RORegBit            
            
            # define I2C 
            i2c = I2C(0)  
            
            # create class with desired functionality
            class FooDevice:
                
                def __init__(self, i2c_bus):
                    self._my_reg_1 = RORegBit(i2c_bus, 68, 5, 1, 5)
                    self._my_reg_2 = RORegBit(i2c_bus, 68, 6, 1, 5)
                    
                def get_my_reg1(self):
                    return self._my_reg_1.__get__()
                    
                def get_my_reg2(self):
                    return self._my_reg_1.__get__()                
                
            # invoke class object  
            device = FooDevice(i2c)

        """
        self._i2c = i2c
        self._dev_addr = dev_addr
        self._reg_addr = reg_addr
        self._num_bytes = num_bytes
        self._bit_location = bit_location
        self._endian = endian
        self._fmt = fmt
        
        __check_reg(self)
        
        del(i2c, dev_addr, reg_addr, num_bytes, bit_location, fmt)
        
    def __get__(self):
        """
        :return: Returns the value of the bit located at :param bit_location:
        :rtype: int()
        """
        return __getbit(self)
    
class RWRegBit:
    def __init__(self, i2c, dev_addr, reg_addr, num_bytes, bit_location, endian='', fmt='B'):
        """
        Creates an :class:`RORegBit` object which allows read and write access to a single bit within a register.             
            
        :param i2c: I2C bus which connects the host system to the peripheral device
        :type kind: machine.I2C()
        :param dev_addr: I2C address of the device which  
        :type dev_addr: int() 
        :param reg_addr: Physical register address which contains the bit of interest  
        :type reg_addr: int() 
        :param num_bytes: Number of bytes to read  
        :type num_bytes: int() 
        :param bit_location: Location of bit within bitfield  
        :type bit_locatin: int() 
        :param endian: Endian-ness of system for which the code is intended to run on. str('') uses native Endian-ness.   
        :type endian: str()
        :param fmt: Format code which is used to unpack data from bytes().  Defaults to 'B' which is good for a single 8-bit register  
        :type fmt: int() 
        
        :return: An initialized RWRegBit object
        :rtype: RWRegBit()
        
        
         **Quickstart: Importing and using the device**

        Here is an example of using the :class:`RWRegBit` class.  
        First you will need to import the following libraries:

        .. code-block:: python
        
            from machine import I2C
            from register.register import RWRegBit

        Once this is done you must define a :class:`machine.I2C` object and then pass that
        to the :class:`RWRegBit` object to instantiate it.
                
        .. code-block:: python

            i2c = I2C(0)  # I2C details are project specific
            
            my_reg = RWRegBit(i2c, 68, 5, 1, 5)
            
        'my_reg' can now provide access to the :method:`__get__() and :method:`__set__().
        Using these methods will get/set the value of the bit found at :param bit_location:.       

        .. code-block:: python
            my_reg.__set__(1) 
            
            print(my_reg.__get__()) # prints 1
        
        Alternatively, a :class:`RWRegBit` object(s) can be placed within another class.

        .. code-block:: python
            # import 
            from machine import I2C
            from register.register import RWRegBit            
            
            # define I2C 
            i2c = I2C(0)  
            
            # create class with desired functionality
            class FooDevice:
                
                def __init__(self, i2c_bus):
                    self._my_reg = RORegBit(i2c_bus, 68, 5, 1, 5)

                def get_my_reg(self):
                    return self._my_reg.__get__()
                    
                def get_my_reg2(self, n):
                    return self._my_reg.__set__(n)
                
            # invoke class object  
            device = FooDevice(i2c)

        """
        self._i2c = i2c
        self._dev_addr = dev_addr
        self._reg_addr = reg_addr
        self._num_bytes = num_bytes
        self._bit_location = bit_location
        self._endian = endian
        self._fmt = fmt
        
        __check_reg(self)
        
        self._premask, self._postmask = __calc_mask(bit_location, bit_location, num_bytes)
        
        del(i2c, dev_addr, reg_addr, num_bytes, bit_location, endian, fmt)
    
    def __get__(self):
        """
        :return: Returns the value of the bit located at :param bit_location:
        :rtype: int()
        """
        return __getbit(self)
    
    def __set__(self, setting):
        """
        :return: Returns 'True' if operation successful 
        :rtype: bool()
        """
        return __setbit(self, setting)
        
class RORegBits:
    def __init__(self, i2c, dev_addr, reg_addr, num_bytes, lsb, msb, endian='', fmt='B'):
        """
        Creates an :class:`RORegBits` object which allows read only access to a sequential set of bits within a bitfield. 
            
        :param i2c: I2C bus which connects the host system to the peripheral device
        :type kind: machine.I2C()
        :param dev_addr: I2C address of the device which  
        :type dev_addr: int() 
        :param reg_addr: Physical register address which contains the bit of interest  
        :type reg_addr: int() 
        :param num_bytes: Number of bytes to read  
        :type num_bytes: int() 
        :param lsb: Location of least significant bit within bitfield  
        :type lsb: int()
        :param msb: Location of most significant bit within bitfield 
        :type msb: int()
        :param endian: Endian-ness of system for which the code is intended to run on. str('') uses native Endian-ness.   
        :type endian: str()
        :param fmt: Format code which is used to unpack data from bytes().  Defaults to 'B' which is good for a single 8-bit register  
        :type fmt: int() 
        
        :return: An initialized RORegBits object
        :rtype: RORegBits()
        
        
         **Quickstart: Importing and using the device**

        Here is an example of using the :class:`RORegBits` class.  
        First you will need to import the following libraries:

        .. code-block:: python
        
            from machine import I2C
            from register.register import RORegBits

        Once this is done you must define a :class:`machine.I2C` object and then pass that
        to the :class:`RORegBits` object to instantiate it.
                
        .. code-block:: python

            i2c = I2C(0)  # I2C details are project specific
            
            my_reg = RORegBits(i2c_bus, 68, 5, 1, 0, 2)
            
        'my_reg' can now provide access to the :method:`__get__().  Using this method
        will return the value of the bit found at :param bit_location:.       

        .. code-block:: python
            
            value = my_reg.__get__() # Returns some value from 0b000 to 0b111
        
        Alternatively, a :class:`RORegBits` object(s) can be placed within another class.

        .. code-block:: python
            # import 
            from machine import I2C
            from register.register import RORegBits            
            
            # define I2C 
            i2c = I2C(0)  
            
            # create class with desired functionality
            class FooDevice:
                
                def __init__(self, i2c_bus):
                    self._my_reg_1 = RORegBits(i2c_bus, 68, 5, 1, 0, 2)
                    self._my_reg_2 = RORegBits(i2c_bus, 68, 6, 1, 3, 6)
                    
                def get_my_reg1(self):
                    return self._my_reg_1.__get__()
                
                @property
                def my_reg2(self):
                    return self._my_reg_2.__get__()
                
            # invoke class object  
            device = FooDevice(i2c)
            
            n1 = device.get_my_reg()
            n2 = device.my_reg2

        """
        self._i2c = i2c
        self._dev_addr = dev_addr
        self._reg_addr = reg_addr
        self._num_bytes = num_bytes
        self._endian = endian
        self._fmt = fmt
        
        __check_reg(self)
        
        self._premask, self._mask, self._postmask = __calc_mask(lsb, msb, num_bytes)        
        
        del(i2c, dev_addr, reg_addr, num_bytes, lsb, msb, endian, fmt)
        
    def __get__(self):
        """
        :return: Returns the value of the bitfield located between :param lsb: and :param msb:
        :rtype: int()
        """
        return __getbits(self)
        
class RWRegBits:
    def __init__(self, i2c, dev_addr, reg_addr, num_bytes, lsb, msb, endian='', fmt='B'):
        """
        Creates an :class:`RWRegBits` object which allows read and write access to a sequential set of bits within a bitfield. 
            
        :param i2c: I2C bus which connects the host system to the peripheral device
        :type kind: machine.I2C()
        :param dev_addr: I2C address of the device which  
        :type dev_addr: int() 
        :param reg_addr: Physical register address which contains the bit of interest  
        :type reg_addr: int() 
        :param num_bytes: Number of bytes to read  
        :type num_bytes: int() 
        :param lsb: Location of least significant bit within bitfield  
        :type lsb: int()
        :param msb: Location of most significant bit within bitfield 
        :type msb: int()
        :param endian: Endian-ness of system for which the code is intended to run on. str('') uses native Endian-ness.   
        :type endian: str()
        :param fmt: Format code which is used to unpack data from bytes().  Defaults to 'B' which is good for a single 8-bit register  
        :type fmt: int() 
        
        :return: An initialized RWRegBits object
        :rtype: RWRegBits()
        
        
         **Quickstart: Importing and using the device**

        Here is an example of using the :class:`RWRegBits` class.  
        First you will need to import the following libraries:

        .. code-block:: python
        
            from machine import I2C
            from register.register import RWRegBits

        Once this is done you must define a :class:`machine.I2C` object and then pass that
        to the :class:`RWRegBits` object to instantiate it.
                
        .. code-block:: python

            i2c = I2C(0)  # I2C details are project specific
            
            my_reg = RWRegBits(i2c_bus, 68, 5, 1, 0, 2)
            
        'my_reg' can now provide access to :method:`__get__() and :method:`__set__().       

        .. code-block:: python
        
            my_reg.__set__(0b110) # Returns some value from 0b000 to 0b111
            value = my_reg.__get__() # Returns 0b110, assuming nothing changes
        
        Alternatively, a :class:`RWRegBits` object(s) can be placed within another class.

        .. code-block:: python
            # import 
            from machine import I2C
            from register.register import RWRegBits            
            
            # define I2C 
            i2c = I2C(0)  
            
            # create class with desired functionality
            class FooDevice:
                
                def __init__(self, i2c_bus):
                    self._my_reg_1 = RWRegBits(i2c_bus, 68, 5, 1, 0, 2)
                    self._my_reg_2 = RWRegBits(i2c_bus, 68, 6, 1, 3, 6)
                    
                def get_my_reg1(self):
                    return self._my_reg_1.__get__()
                
                def set_my_reg1(self, n):
                    return self._my_reg_1.__set__(n)
                
                @property
                def my_reg2(self):
                    return self._my_reg_2.__get__()
                    
                @my_reg2.setter
                def my_reg2(self, n):
                    return self._my_reg_2.__set__(n)
                
            # invoke class object  
            device = FooDevice(i2c)
            
            device.set_my_reg(0b110)
            print(device.get_my_reg()) # prints 6
            
           device.my_reg2 = 0b110
           print(device.my_reg2) # prints 6

        """
        self._i2c = i2c
        self._dev_addr = dev_addr
        self._reg_addr = reg_addr
        self._num_bytes = num_bytes
        self._endian = endian
        self._fmt = fmt
        
        __check_reg(self)
        
        self._premask, self._mask, self._postmask = __calc_mask(lsb, msb, num_bytes)  
            
        del(i2c, dev_addr, reg_addr, num_bytes, lsb, msb, fmt, endian)
        
    def __get__(self):
        """
        :return: Returns the value of the bitfield located between :param lsb: and :param msb:
        :rtype: int()
        """
        return __getbits(self)
    
    def __set__(self, setting):
        """
        :return: True if successful
        :rtype: bool()
        """
        return __setbits(self, setting)       
        
class ROReg:
    def __init__(self, i2c, dev_addr, reg_addr, num_bytes=1, endian='', fmt='B'):
        """
        Creates a :class:`ROReg` object which allows read only access to n number of sequential registers,
        where n is specified by :param num_bytes:. 
            
            
        :param i2c: I2C bus which connects the host system to the peripheral device
        :type kind: machine.I2C()
        :param dev_addr: I2C address of the device which  
        :type dev_addr: int() 
        :param reg_addr: Physical register address which contains the bit of interest  
        :type reg_addr: int() 
        :param num_bytes: Number of bytes to read. Defaults to 1.
        :type num_bytes: int() 
        :param fmt: Format code which is used to unpack data from bytes().  Defaults to 'B'.  
        :type fmt: int() 
        
        :return: An initialized ROReg object
        :rtype: ROReg()
        
        
         **Quickstart: Importing and using the device**

        Here is an example of using the :class:`ROReg` class.  
        First you will need to import the following libraries:

        .. code-block:: python
        
            from machine import I2C
            from register.register import ROReg

        Once this is done you must define a :class:`machine.I2C` object and then pass that
        to the :class:`ROReg` object to instantiate it.
                
        .. code-block:: python

            i2c = I2C(0)  # I2C details are project specific
            
            my_reg = ROReg(i2c, 68, 5)
            
        'my_reg' can now provide access to the :method:`__get__().  Using this method
        will return the value of the bit found at :param bit_location:.       

        .. code-block:: python
            
            value = my_reg.__get__() # some value between 0b0 and 0b1111_1111
        
        Alternatively, a :class:`ROReg` object(s) can be placed within another class.

        .. code-block:: python
            # import 
            from machine import I2C
            from register.register import ROReg            
            
            # define I2C 
            i2c = I2C(0)  
            
            # create class with desired functionality
            class FooDevice:
                
                def __init__(self, i2c_bus):
                    self._my_reg_1 = ROReg(i2c_bus, 68, 5)
                    self._my_reg_2 = ROReg(i2c_bus, 68, 6)
                    
                def get_my_reg1(self):
                    return self._my_reg_1.__get__()
                
                @property
                def my_reg2(self):
                    return self._my_reg_1.__get__()                
                
            # invoke class object  
            device = FooDevice(i2c)
            
            print(device.get_my_reg1())
            print(device.my_reg2)

        """
        self._i2c = i2c
        self._dev_addr = dev_addr
        self._reg_addr = reg_addr
        self._num_bytes = num_bytes
        self._fmt = fmt
        self._endian = endian
        
        __check_reg(self)
        
        del(i2c, dev_addr, reg_addr, num_bytes, fmt, endian)
    
    def __get__(self):
        """
        :return: Returns tuple containing n number of elements, where n is the number of characters in :param fmt:
        :rtype: tuple()
        """
        return __getreg(self)
        
class RWReg:
    """
        Creates a :class:`RWReg` object which allows read and write access to n number of sequential registers,
        where n is specified by :param num_bytes:.             
            
        :param i2c: I2C bus which connects the host system to the peripheral device
        :type kind: machine.I2C()
        :param dev_addr: I2C address of the device which  
        :type dev_addr: int() 
        :param reg_addr: Physical register address which contains the bit of interest  
        :type reg_addr: int() 
        :param num_bytes: Number of bytes to read. Defaults to 1.
        :type num_bytes: int() 
        :param fmt: Format code which is used to unpack data from bytes().  Defaults to 'B'.  
        :type fmt: int() 
        
        :return: An initialized RWReg object
        :rtype: RWReg()
        
        
         **Quickstart: Importing and using the device**

        Here is an example of using the :class:`RWReg` class.  
        First you will need to import the following libraries:

        .. code-block:: python
        
            from machine import I2C
            from register.register import RWReg

        Once this is done you must define a :class:`machine.I2C` object and then pass that
        to the :class:`RWReg` object to instantiate it.
                
        .. code-block:: python

            i2c = I2C(0)  # I2C details are project specific
            
            my_reg = RWReg(i2c, 68, 5)
            
        'my_reg' can now provide access to the :method:`__get__() and __set__().       

        .. code-block:: python
            my_reg.__set__(0b0)
            value = my_reg.__get__() # 0b0 if nothing changed
        
        Alternatively, a :class:`RWReg` object(s) can be placed within another class.

        .. code-block:: python
            # import 
            from machine import I2C
            from register.register import RWReg            
            
            # define I2C 
            i2c = I2C(0)  
            
            # create class with desired functionality
            class FooDevice:
                
                def __init__(self, i2c_bus):
                    self._my_reg_1 = RWReg(i2c_bus, 68, 5)
                    self._my_reg_2 = RWReg(i2c_bus, 68, 6)
                    
                def get_my_reg1(self):
                    return self._my_reg_1.__get__()
                
                def set_my_reg1(self, n):
                    return self._my_reg_1.__set__(n)
                
                @property
                def my_reg2(self):
                    return self._my_reg_1.__get__()
                
                @my_reg2.setter
                def my_reg2(self, n):
                    return self._my_reg_1.__set__(n)
                
                
            # invoke class object  
            device = FooDevice(i2c)
            
            device.set_my_reg1(0b110)
            print(device.get_my_reg1()) # prints 6, assuming nothing changed
            
            device.my_reg2 = 0b1111_0000
            print(device.my_reg2) # prints 240

        """
    def __init__(self, i2c, dev_addr, reg_addr, num_bytes, endian='', fmt='B'):
        self._i2c = i2c
        self._dev_addr = dev_addr
        self._reg_addr = reg_addr
        self._num_bytes = num_bytes
        self._fmt = fmt
        self._endian = endian
        
        __check_reg(self)
        
        del(i2c, dev_addr, reg_addr, num_bytes, fmt, endian)
    
    def __get__(self):
        """
        :return: Returns tuple containing n number of elements, where n is the number of characters in :param fmt:
        :rtype: tuple()
        """
        return __getreg(self)
    
    def __set__(self, setting):
        """
        :param setting: Value(s) to be written to register(s).  Order must match :param fmt:.
        :type setting: int(), bytes(), bytearray(), or list/tuple containing those values in order 
        :return: Returns True if operation successful
        :rtype: tuple()
        """
        return __setreg(self, setting)
    
"""
*
* GLOBAL HELPER FUNCTIONS
*
*
"""
def __getbit(reg_object):
    if isinstance(reg_object, (RORegBit, RWRegBit)):
        # Retrieve register value and unpack to int
        value = reg_object._i2c.readfrom_mem(reg_object._dev_addr, reg_object._reg_addr, reg_object._num_bytes)
        
        # Unpack byte
        value = unpack(reg_object._endian+reg_object._fmt, value)[0]
        
        # Perform shift followed by _AND_ operation to determine bit state        
        return (value >> reg_object._bit_location)&0b1        
                    
    else:
         raise TypeError("incorrect object type - must be RORegBit, RWRegBit")
        
def __setbit(reg_object, setting):
    if isinstance(reg_object, RWRegBit):
        if setting in (0,1):
            # Retrieve register value and unpack to int
            value = reg_object._i2c.readfrom_mem(reg_object._dev_addr, reg_object._reg_addr, reg_object._num_bytes)
            
            # Unpack byte
            value = unpack(reg_object._endian+reg_object._fmt, value)[0]
            
            # Assemble byte
            value = (value&reg_object._postmask) + (setting<<reg_object._bit_location) + (value&reg_object._premask)
            
            # Pack to bytes
            value = pack(reg_object._endian+reg_object._fmt, value)
            
            # Write to I2C
            reg_object._i2c.writeto_mem(reg_object._dev_addr, reg_object._reg_addr, value)
            
            # Return True for success        
            return True
        
        else:
            raise ValueError("setting must be int(0) or int(1)")                    
    else:
        raise TypeError("incorrect object type - must be RWRegBit")
        
def __getbits(reg_object):
    if isinstance(reg_object, (RORegBits, RWRegBits)):    
        # Retrieve register value and unpack to int
        value = reg_object._i2c.readfrom_mem(reg_object._dev_addr, reg_object._reg_addr, reg_object._num_bytes)
        
        # Unpack bytes
        value = unpack(reg_object._endian+reg_object._fmt, value)[0]       
        
        # Return value of bit field
        return (value & reg_object._mask)>>reg_object._lsb       
                    
    else:
         raise TypeError("incorrect object type - must be RORegBits, RWRegBits")
        
def __setbits(reg_object, setting):
    if isinstance(reg_object, RWRegBits): 
        if isinstance(setting, int) and setting <= reg_object._mask:
        
            # Retrieve register value and unpack to int
            value = reg_object._i2c.readfrom_mem(reg_object._dev_addr, reg_object._reg_addr, reg_object._num_bytes)
            
            # Unpack bytes
            value = unpack(reg_object._endian+reg_object._fmt, value)[0]
            
            # Assemble  
            value = (value&reg_object._postmask) + (setting<<reg_object._lsb) + (value&reg_object._premask)
            
            # Pack to bytes object
            value = struct.pack(reg_object._endian+reg_object._fmt, value)
            
            # Write to device
            reg_object._i2c.writeto_mem(reg_object._dev_addr, reg_object._reg_addr, value)
            
            return True
        
        else:
            raise ValueError(f"value of setting exceeds max value of bitfield: {reg_object._mask}")    
    else:
        raise TypeError("incorrect object type - must be RWRegBits")

def __getreg(reg_object):
    if isinstance(reg_object, (ROReg, RWReg)):
        # Retrieve register value and unpack to int
        values = reg_object._i2c.readfrom_mem(reg_object._dev_addr, reg_object._reg_addr, reg_object._num_bytes)        
                
        # Return Tuple of values
        return unpack(reg_object._endian+reg_object._fmt, values)   
                    
    else:
         raise TypeError("incorrect object type - must be ROReg, RWReg")
        
def __setreg(reg_object, settings):
    
    if isinstance(reg_object, RWReg):
        if isinstance(settings, (bytes, bytearray)):
                # Write to device
                reg_object._i2c.writeto_mem(reg_object._dev_addr, reg_object._reg_addr, settings)
                
                
        elif isinstance(settings, (tuple, list)):
            # Where our data will go
            d = bytearray()
            
            # Pack and append to d
            for n in range(0, len(settings)):
                d.extend(pack(reg_object._endian+reg_object._fmt[n] ,settings[n]))
            
            # Write to device
            reg_object._i2c.writeto_mem(reg_object._dev_addr, reg_object._reg_addr, d)                      
            
        # Assumed single int() for single reg-op
        elif isinstance(settings, int):
            d = pack(reg_object._endian+reg_object._fmt ,settings)
            reg_object._i2c.writeto_mem(reg_object._dev_addr, reg_object._reg_addr, d)            
               
        else:
            raise TypeError("unsupported object type, settings must be int(), bytes(), bytearray(), tuple(), or list()")                    
    else:
         raise TypeError("incorrect object type - must be ROReg, RWReg")
        
def __calc_mask(lsb, msb, numbytes):
    """
    Takes in full description of bitfield that needs masking
    
    returns ints() pre, mask, post
    """
    
    # Check input types
    if lsb.__class__() == int() and lsb >= 0:
        if msb.__class__() == int() and msb >= 0:
            if numbytes.__class__() == int() and numbytes >= 0: 
                
                # Check for detectable errors
                if msb>=lsb:
                    
                    # Single bit mask
                    if msb == lsb:
                        pre, post = 0b0, 0b0
                        
                        # Calc post masking
                        for bit in range(msb+1, numbytes*8):
                            post = (post<<1) + 0b1
                        
                        # Calc pre masking
                        for bit in range(0, lsb):
                                    pre = (pre<<1) + 0b1
                        
                        return pre, post
                        
                    # Multibit mask
                    else:
                            
                        # Values to return
                        pre, mask, post = 0b0, 0b0, 0b0
                            
                        # Calc post masking
                        for bit in range(msb+1, numbytes*8):
                            post = (post<<1) + 0b1
                                
                        # Calc bitfield masking
                        for bit in range(lsb, msb+1):
                            mask = (mask<<1) + 0b1
                            
                        # No bits lower than 0
                        if lsb == 0:
                            return 0b0, mask, post
                            
                        else:
                            for bit in range(0, lsb):
                                pre = (pre<<1) + 0b1
                                    
                            return pre, mask, post                  
                else:
                    raise ValueError("msb must be greater than or equal to lsb")
            else:
                raise ValueError("numbytes must be of type int() and 0 or greater")
        else:
            raise ValueError("msb must be of type int() and 0 or greater")
    else:
        raise ValueError("lsb must be of type int() and 0 or greater")

def __check_reg(reg_object):
    
    # Alowable struct.pack/unpack formats to check for
    fmts = {'b':1, 'B':1, 'h':2, 'H':2, 'f':4, 'i':4, 'I':4, 'l':4, 'L':4, 'q':8, 'Q':8}    
    endians = '@><'
    byte_count = 0
    
    # Take in only register objects
    if isinstance(reg_object, (RORegBit, RWRegBit, RORegBits, RWRegBits, ROReg, RWReg)):
        
        # Make sure they are strings
        if type(reg_object._fmt) == str and type(reg_object._endian) == str:
            
            # Check each letter in format string, To see if allowable
            for n in range(0, len(reg_object._fmt)):
                if reg_object._fmt[n] in fmts:                    
                    # Add corresonding byte length to verify _num_bytes and format string agree
                    byte_count = byte_count + fmts[reg_object._fmt[n]]          
    
                else:
                    raise ValueError(f"unsupported format code of '{reg_object._fmt[n]}'")
                
            if byte_count != reg_object._num_bytes:
                raise ValueError(f"format string accounts for {byte_count} bytes, _num_bytes value of {reg_object._num_bytes} does not match")              
                    
        else:
            raise TypeError("format and endian must be of type str()")
    else:
        raise TypeError("incorrect object type - must be ROReg, RWReg, ROBits, RWBits, ROReg, RWReg")

class Transaction:
    """
    The user can supply a transaction object with a list of any number of
    Register objects. The Transaction object will then perform one I2C
    transaction and return all data as a list OR perform all write operations.
    
    1) The Register objects should all be from one physical I2C device
    2) True = Read, False = Write (Default is read)
    3) Reads can be from non-sequential registers
    4) Writes can be made only to sequential registers OR more than one
       transaction will be generated
    
    i.e.
    
    # Define Register objects
    register1 = ROBits()
    register2 = ROBits()
    register3 = ROBits()
    
    # Create list object containing only Register objects
    list_of_registers = [register1, register2, register3]
    
    # Instantiate Transaction object
    data_from_device = Transaction(list_of_registers)
    
    # Retrieve data
    data = data_from_device.__get__()
    
    # Use data as desired
    datapoint_1 = data_from_device[0]
    datapoint_2 = data_from_device[1]
    datapoint_3 = data_from_device[2]
    """
    
    
    def __init__(self, read_or_write:bool = True, list_of_registers:list() =[]):
        # Data
        self.__list_of_registers = list_of_registers
        
        # Check if it is a list
        if self.__list_of_registers.__class__() == list():            
            
            for reg in self.__list_of_registers:
                # Check each element against all possible Register types
                if self.__list_of_registers[reg].__class__() in [RORegBit, RORegBits, RWRegBit, RWRegBits, RORegStruct]:
                    pass
                    
                else:
                    # Error - list_element[reg] not a register object
                    pass
        
        else:
            # Error - list_of_registers object must be list()
            pass
                
    def add_reg(self, reg_object):
        """
        This function allows for register objects to be added to an already
        instantiated Transaction object
        """
        if reg_object.__class__() in [RORegBit, RORegBits, RWRegBit, RWRegBits, RORegStruct]:
            self.__list_of_registers.append(reg_object)
            
            self._order_list()
            
        else:
            # Error - reg object of incorrect type()
            pass
        
    def rem_reg(self, index):
        """
        This function allows for a register object to be removed from an
        already instantiated transaction object
        """        
        if index in range(0, len(self.__list_of_registers)):
            # Remove element 
            self.__list_of_registers.remove(index)
        else:
            # Error - index out of bounds
            pass
        
    def order_list(self):        
        """        
        Sorts list of registers by register address            
        """
        self.__list_of_registers = sorted(self.__list_of_registers, key=lambda reg:reg.reg_addr)
        
    def data(self):
        """
        Performs 1 i2c transaction and returns data as list
        """
            
        
            
            
        
            
                 
        
                 
        
        
