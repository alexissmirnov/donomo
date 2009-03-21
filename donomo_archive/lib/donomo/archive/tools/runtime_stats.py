from django.conf            import settings
from donomo.archive.utils   import sqs
from boto.ec2               import connection
import sys

"""
Prints the number of running instances OR the number of messages in the queue
depending on the input paramater (instances or pending)
"""

def main():
    if sys.argv[1] == 'pending':
        print sqs._get_queue().count()
    elif sys.argv[1] == 'instances':
        c = connection.EC2Connection(
                                settings.AWS_ACCESS_KEY_ID, 
                                settings.AWS_SECRET_ACCESS_KEY)
        print len(c.get_all_instances())
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()