import logging
from functools import wraps

LOGGER = logging.getLogger(__name__)

def print_stack(func):
    @wraps(func)
    def tmp(*args, **kwargs):
        print(func.__name__)
        return func(*args, **kwargs)
    return tmp

def print_caller_name(stack_size=3):
    def wrapper(fn):
        def inner(*args, **kwargs):
            import inspect
            stack = inspect.stack()

            modules = [(index, inspect.getmodule(stack[index][0]))
                       for index in reversed(range(1, stack_size))]
            module_name_lengths = [len(module.__name__)
                                   for _, module in modules]

            s = '{index:>5} : {module:^%i} : {name}' % (max(module_name_lengths) + 4)
            callers = ['',
                       s.format(index='level', module='module', name='name'),
                       '-' * 50]

            for index, module in modules:
                callers.append(s.format(index=index,
                                        module=module.__name__,
                                        name=stack[index][3]))

            callers.append(s.format(index=0,
                                    module=fn.__module__,
                                    name=fn.__name__))
            callers.append('')
            print('\n'.join(callers))

            fn(*args, **kwargs)
        return inner
    return wrapper