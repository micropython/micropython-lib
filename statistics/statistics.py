def mean(data):
	average = 0
	for points in data:
		average += points
	return average/len(data)
	
def median(data):
	"""Return median of sequence data."""
	sorteddata = sorted(data)
	dataLen = len(data)
	index = (dataLen - 1) // 2

	if (dataLen % 2):
		return sorteddata[index]
	else:
		return (sorteddata[index] + sorteddata[index + 1])/2.0
		
def mode(data):
	"""Return mode of sequence data."""
	return max(set(data), key=data.count)
	
def _ss(data):
	"""Return sum of square deviations of sequence data."""
	c = mean(data)
	ss = sum((x-c)**2 for x in data)
	return ss
	
def pstdev(data):
	"""Calculates the population standard deviation."""
	n = len(data)
	if n < 2:
		raise ValueError('variance requires at least two data points')
	ss = _ss(data)
	pvar = ss/n # the population variance
	return pvar**0.5

def variance(data):
	"""Calculates variance."""
	if iter(data) is data:
		data = list(data)
	n = len(data)
	if n < 2:
		raise ValueError('variance requires at least two data points')
	T, ss = _ss(data)
	return _convert(ss/(n-1), T)
