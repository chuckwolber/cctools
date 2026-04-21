class Allocation():
    """Single-entry style expense allocation.

    Categorize an expense single-entry style. No distinction is made between
    the various double entry categories (asset, liability, capital, revenue,
    expense) or types (CREDIT, DEBIT).

    Amounts are presented to the user in terms they are used to seeing on a
    traditional credit card statement. Negative values signify a reduction in
    one's outstanding debt, such as a payment. Positive values signify an
    increase in one's outstanding debt, usually stemming from a purchase or an
    interest charge.

    To avoid confusion, allocations can only be made using the same sign
    presented to the user. For example, a transaction amount of $10 may not be
    be allocated as $1000 to one category and -$990 to another category.
    """
    allocation: list
    negative: bool
    amount_orig: float
    amount_curr: float

    ALLOC_COLUMNS = None
    ALLOC_COLUMNS_MAP = None

    @classmethod
    def init_cols(cls, alloc_columns: list) -> None:
        cls.ALLOC_COLUMNS = alloc_columns

    @classmethod
    def init_cols_map(cls, alloc_columns_map: list) -> None:
        cls.ALLOC_COLUMNS_MAP = alloc_columns_map

    @classmethod
    def __print_cols_map_for_key(cls, key: str) -> None:
        print("\t" + key + ":\t" + cls.ALLOC_COLUMNS_MAP[key])

    @classmethod
    def print_cols_map(cls, key: str = None):
        if cls.ALLOC_COLUMNS_MAP == None:
            return
        if key == None:
            for key in cls.ALLOC_COLUMNS_MAP.keys():
                cls.__print_cols_map_for_key(key)
        else:
            cls.__print_cols_map_for_key(key)

    def __init__(self, amount: float):
        if self.ALLOC_COLUMNS is None:
            raise ValueError("Error: Allocation class not initialized. Call `initialize` first.")
        if not isinstance(amount, float):
            raise ValueError("Error: Amount is not a floating point value.")
        self.allocation = [0.0] * len(self.ALLOC_COLUMNS)
        self.amount_orig = float(-1*amount)
        self.amount_curr = self.amount_orig
        self.negative = False
        if self.amount_orig < 0:
            self.negative = True

    def get_paired_allocations(self) -> str:
        """Pair column categories.

        Pair column categories with current amounts allocated to each category.
        Omit the allocation amount if it is zero.
        """
        paired = [f"{a}({b})" if b != 0 else a for a, b in zip(self.ALLOC_COLUMNS, self.allocation)]
        if self.ALLOC_COLUMNS_MAP != None:
            paired.append('?')
        return f"[{', '.join(paired)}]"

    def to_list(self) -> list:
        return ['' if x == 0 else x for x in self.allocation]

    def get_allocations_sum(self) -> float:
        return round(sum(self.allocation),2)

    def __is_valid_category(self, category: str) -> bool:
        if category in self.ALLOC_COLUMNS:
            return True
        return False

    def allocate_amount(self, category: str, amount: str = None):
        """Allocate an amount to a specific category.

        Allocation amounts must be the same sign as the transaction amount.
        The transaction amount can be applied to multiple categories until the
        entire transaction amount is allocated. If the amount argument is
        'None' the remaining unallocated amount is assumed. If a category has
        an amount already allocated to it, the allocated value is added back to
        the unallocated amount before a new allocation is applied.

        Keyword arguments:
        category -- the category to assign the amount
        amount -- the currency value to assign to the category
        """
        if not self.__is_valid_category(category):
            return
        index = self.ALLOC_COLUMNS.index(category)

        x = self.amount_curr
        if amount != None:
            try:
                x = float(amount)
            except ValueError:
                return

        # Allocation amount must have the same sign as the transaction amount.
        if (self.negative and x > 0) or (not self.negative and x < 0):
            return

        # Reset over allocation to the current outstanding amount.
        if self.negative and x < self.amount_curr:
            x = self.amount_curr
        elif not self.negative and x > self.amount_curr:
            x = self.amount_curr

        # Recover currently allocated amount before allocating a new amount.
        self.amount_curr += self.allocation[index]

        self.amount_curr = round(self.amount_curr - x, 2)
        self.allocation[index] = x