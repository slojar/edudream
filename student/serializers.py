"""
{
                "dob": student.dob,
                "grade": student.grade,
                "address": parent.address,
                "city_id": parent.city_id,
                "state_id": parent.state_id,
                "country_id": parent.country_id,
                "city_name": parent.city.name,
                "state_name": parent.state.name,
                "country_name": parent.country.name,
                "parent_name": str("{} {}").format(parent.user.first_name, parent.user.last_name).capitalize(),
                "parent_email": parent.user.email,
                "parent_mobile": parent.mobile_number
            }
"""



