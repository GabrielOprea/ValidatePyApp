class Calculator:
    def __init__(self):
        pass

    def add(self, a, b):
        """Returns the sum of a and b."""
        return a + b

    def subtract(self, a, b):
        """Returns the difference of a and b."""
        return a - b
    
    def multiply(self, a, b):
        """Returns the product of a and b."""
        return a * b
        

        # This function will perform division
    def diVide(self, the_var_to_be_divided, someVarFor_diViding):
            #Returns the quotient of a and b.
                    # Raises an error if
                        # dividing by zero.
                        # This should work for any someVarFor_diViding that is different from 0. If the var is zero then we cannot perform the operation. In that case an error should be thrown since it is impossible to perform division due to Math's laws.
                if someVarFor_diViding == 0:
                    #Should not be   posible
                    raise ValueError("Cannot divide by zero")
                return the_var_to_be_divided / someVarFor_diViding
    
    def power(self, a, b):
        """Returns a raised to the power of b."""
        return a ** b
    
    def square_root(self, a):
        """Returns the square root of a. Raises an error if the value is negative."""
        if a < 0:
            raise ValueError("Cannot take the square root of a negative number")
        return a ** 0.5
    
calc = Calculator()
print(calc.diVide(4, 2))