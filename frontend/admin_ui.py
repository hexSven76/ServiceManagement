import pandas as pd
import streamlit as st

from frontend.admin_helpers import (
    change_admin_user_role,
    delete_admin_service,
    fetch_admin_bookings,
    fetch_admin_reviews,
    fetch_admin_services,
    fetch_admin_stats,
    fetch_admin_users,
    force_cancel_admin_booking,
    force_confirm_admin_booking,
    set_admin_user_active,
    update_admin_service,
    update_admin_service_status,
)
from frontend.components import page_title
from frontend.report_helpers import admin_stats_pdf_bytes, customer_bookings_pdf_bytes, provider_bookings_pdf_bytes
from frontend.ui_helpers import format_datetime, format_price_irr, show_action_error, status_to_table_text


def render_admin_page(selected_page: str):
    if selected_page == "Dashboard":
        render_admin_dashboard()
    elif selected_page == "Users":
        render_admin_users()
    elif selected_page == "Services":
        render_admin_services()
    elif selected_page == "Bookings":
        render_admin_bookings()
    elif selected_page == "Reviews":
        render_admin_reviews()
    elif selected_page == "Reports":
        render_admin_reports()
    else:
        st.error("Admin page not found.")


def render_admin_dashboard():
    page_title("Admin Dashboard", "System-level KPIs, charts, and top services.")
    try:
        stats = fetch_admin_stats(st.session_state.user_id)
    except Exception as error:
        show_action_error(error)
        return

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Users", stats.get("total_users", 0))
    col2.metric("Total Bookings", stats.get("total_bookings", 0))
    col3.metric("Today", stats.get("today_bookings", 0))
    col4.metric("This Week", stats.get("week_bookings", 0))
    col5.metric("Income", format_price_irr(stats.get("fake_income", 0)))

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.subheader("Users by Role")
        st.bar_chart(pd.DataFrame({"count": stats.get("users_by_role", {})}).T)
    with chart_col2:
        st.subheader("Services by Status")
        st.bar_chart(pd.DataFrame({"count": stats.get("services_by_status", {})}).T)

    st.subheader("Top Services")
    top_services = stats.get("top_services", [])
    if top_services:
        st.dataframe(pd.DataFrame(top_services), use_container_width=True, hide_index=True)
    else:
        st.info("No service booking data yet.")


def _filter_rows(rows: list[dict], search_text: str, keys: list[str]) -> list[dict]:
    query = search_text.strip().lower()
    if not query:
        return rows
    result = []
    for row in rows:
        text = " ".join(str(row.get(key) or "") for key in keys).lower()
        if query in text:
            result.append(row)
    return result


def render_admin_users():
    page_title("User Management", "Manage customers, providers, and admin visibility safely.")

    try:
        users = fetch_admin_users(st.session_state.user_id)
    except Exception as error:
        show_action_error(error)
        return

    role_filter = st.selectbox(
        "Role",
        ["All", "ADMIN", "PROVIDER", "CUSTOMER"],
        key="admin_user_role_filter",
    )

    search = st.text_input(
        "Search username/email/name",
        key="admin_user_search_filter",
    )

    rows = [
        user for user in users
        if role_filter == "All" or user.get("role") == role_filter
    ]

    rows = _filter_rows(
        rows,
        search,
        ["username", "email", "full_name", "phone"],
    )

    tab_all, tab_providers, tab_customers = st.tabs(
        ["All Users", "Providers", "Customers"]
    )

    with tab_all:
        render_users_table_and_actions(rows, key_prefix="all")

    with tab_providers:
        render_users_table_and_actions(
            [user for user in rows if user.get("role") == "PROVIDER"],
            key_prefix="providers",
        )

    with tab_customers:
        render_users_table_and_actions(
            [user for user in rows if user.get("role") == "CUSTOMER"],
            key_prefix="customers",
        )


def render_users_table_and_actions(users: list[dict], key_prefix: str):
    if not users:
        st.info("No users found.")
        return
    table = [
        {
            "ID": u.get("id"),
            "Username": u.get("username"),
            "Email": u.get("email"),
            "Role": u.get("role"),
            "Active": "Yes" if u.get("is_active") else "No",
            "Full Name": u.get("full_name") or "-",
            "Phone": u.get("phone") or "-",
            "Created": format_datetime(u.get("created_at")),
        }
        for u in users
    ]
    st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)

    for user in users:
        with st.expander(f"Manage {user.get('username')} | #{user.get('id')}"):
            col1, col2 = st.columns(2)
            with col1:
                if user.get("id") == st.session_state.user_id:
                    st.caption("Self-lockout protection: your own account cannot be deactivated or role-changed here.")
                if st.button(
                    "Deactivate" if user.get("is_active") else "Activate",
                    key=f"{key_prefix}_toggle_user_{user.get('id')}",
                    disabled=user.get("id") == st.session_state.user_id,
                    use_container_width=True,
                ):
                    try:
                        set_admin_user_active(st.session_state.user_id, user.get("id"), not user.get("is_active"))
                        st.rerun()
                    except Exception as error:
                        show_action_error(error)
            with col2:
                new_role = st.selectbox(
                    "Role",
                    ["ADMIN", "PROVIDER", "CUSTOMER"],
                    index=["ADMIN", "PROVIDER", "CUSTOMER"].index(user.get("role")),
                    key=f"{key_prefix}_role_{user.get('id')}",
                    disabled=user.get("id") == st.session_state.user_id,
                )
                if st.button(
                    "Change Role",
                    key=f"{key_prefix}_change_role_{user.get('id')}",
                    disabled=user.get("id") == st.session_state.user_id or new_role == user.get("role"),
                    use_container_width=True,
                ):
                    try:
                        change_admin_user_role(st.session_state.user_id, user.get("id"), new_role)
                        st.rerun()
                    except Exception as error:
                        show_action_error(error)


def render_admin_services():
    page_title(
        "Service Management",
        "View, filter, edit, activate/deactivate, and delete services.",
    )

    try:
        services = fetch_admin_services(st.session_state.user_id)
    except Exception as error:
        show_action_error(error)
        return

    if not services:
        st.info("No services found.")
        return

    filtered = render_admin_service_filters(services)

    if not filtered:
        st.info("No services match the selected filters.")
        return

    render_admin_services_table(filtered)
    render_admin_service_cards(filtered)


def render_admin_service_filters(services: list[dict]) -> list[dict]:
    st.subheader("Service Filters")

    categories = sorted({s.get("category") for s in services if s.get("category")})
    providers = sorted({s.get("provider_name") for s in services if s.get("provider_name")})
    prices = [float(s.get("price") or 0) for s in services]
    max_existing_price = max(prices) if prices else 0.0

    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.selectbox(
            "Status",
            ["All", "ACTIVE", "INACTIVE"],
            key="admin_service_status_filter",
        )

    with col2:
        category_filter = st.selectbox(
            "Category",
            ["All"] + categories,
            key="admin_service_category_filter",
        )

    with col3:
        provider_filter = st.selectbox(
            "Provider",
            ["All"] + providers,
            key="admin_service_provider_filter",
        )

    price_col1, price_col2, search_col = st.columns(3)

    with price_col1:
        min_price = st.number_input(
            "Min Price",
            min_value=0.0,
            value=0.0,
            step=10.0,
            key="admin_service_min_price_filter",
        )

    with price_col2:
        max_price = st.number_input(
            "Max Price",
            min_value=0.0,
            value=float(max_existing_price),
            step=10.0,
            key="admin_service_max_price_filter",
        )

    with search_col:
        search = st.text_input(
            "Search",
            placeholder="Service, provider, category, description...",
            key="admin_service_search_filter",
        )

    if max_price < min_price:
        st.warning("Max price cannot be lower than min price.")
        return []

    filtered = []

    for service in services:
        price = float(service.get("price") or 0)

        if status_filter != "All" and service.get("status") != status_filter:
            continue

        if category_filter != "All" and service.get("category") != category_filter:
            continue

        if provider_filter != "All" and service.get("provider_name") != provider_filter:
            continue

        if price < min_price or price > max_price:
            continue

        filtered.append(service)

    filtered = _filter_rows(
        filtered,
        search,
        ["title", "provider_name", "category", "description"],
    )

    st.caption(f"Showing {len(filtered)} of {len(services)} services.")

    return filtered


def render_admin_services_table(services: list[dict]):
    table_data = [
        {
            "ID": service.get("id"),
            "Title": service.get("title"),
            "Provider": service.get("provider_name"),
            "Category": service.get("category"),
            "Price": format_price_irr(service.get("price")),
            "Duration": service.get("duration_minutes"),
            "Status": service.get("status"),
        }
        for service in services
    ]

    st.dataframe(
        pd.DataFrame(table_data),
        use_container_width=True,
        hide_index=True,
    )


def render_admin_service_cards(services: list[dict]):
    for service in services:
        service_id = service.get("id")

        with st.expander(f"Manage service #{service_id} — {service.get('title')}"):
            render_admin_service_edit_form(service)

            st.markdown("---")

            col1, col2 = st.columns(2)

            with col1:
                new_status = "INACTIVE" if service.get("status") == "ACTIVE" else "ACTIVE"

                if st.button(
                    f"Set {new_status}",
                    key=f"admin_toggle_service_{service_id}",
                    use_container_width=True,
                ):
                    try:
                        update_admin_service_status(
                            st.session_state.user_id,
                            service_id,
                            new_status,
                        )
                        st.success(f"Service set to {new_status}.")
                        st.rerun()
                    except Exception as error:
                        show_action_error(error)

            with col2:
                confirm = st.checkbox(
                    "Confirm delete",
                    key=f"admin_delete_service_confirm_{service_id}",
                )

                if st.button(
                    "Delete Service",
                    key=f"admin_delete_service_{service_id}",
                    disabled=not confirm,
                    use_container_width=True,
                ):
                    try:
                        delete_admin_service(st.session_state.user_id, service_id)
                        st.success("Service deleted.")
                        st.rerun()
                    except Exception as error:
                        show_action_error(error)


def render_admin_service_edit_form(service: dict):
    service_id = service.get("id")

    with st.form(f"admin_edit_service_form_{service_id}"):
        st.caption(
            f"Provider: {service.get('provider_name')} | "
            f"Provider ID: {service.get('provider_id') or '-'}"
        )

        title = st.text_input(
            "Service Title",
            value=service.get("title") or "",
            key=f"admin_edit_service_title_{service_id}",
        )

        category = st.text_input(
            "Category",
            value=service.get("category") or "Uncategorized",
            key=f"admin_edit_service_category_{service_id}",
        )

        description = st.text_area(
            "Description",
            value=service.get("description") or "",
            key=f"admin_edit_service_description_{service_id}",
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            price = st.number_input(
                "Price",
                min_value=0.0,
                step=10.0,
                value=float(service.get("price") or 0),
                key=f"admin_edit_service_price_{service_id}",
            )

        with col2:
            duration = st.number_input(
                "Duration",
                min_value=1,
                step=5,
                value=int(service.get("duration_minutes") or service.get("duration") or 1),
                key=f"admin_edit_service_duration_{service_id}",
                help="Duration in minutes.",
            )

        with col3:
            status = st.selectbox(
                "Status",
                ["ACTIVE", "INACTIVE"],
                index=0 if service.get("status") == "ACTIVE" else 1,
                key=f"admin_edit_service_status_{service_id}",
            )

        submitted = st.form_submit_button("Save Service Changes")

    if submitted:
        if not title.strip():
            st.warning("Service title is required.")
            return

        try:
            update_admin_service(
                admin_id=st.session_state.user_id,
                service_id=service_id,
                title=title.strip(),
                description=description.strip(),
                category=category.strip() or "Uncategorized",
                price=float(price),
                duration=int(duration),
                status=status,
            )

            st.success("Service updated successfully.")
            st.rerun()

        except Exception as error:
            show_action_error(error)


def render_admin_bookings():
    page_title(
        "Booking Management",
        "View, filter, and force-control all bookings.",
    )

    try:
        bookings = fetch_admin_bookings(st.session_state.user_id)
    except Exception as error:
        show_action_error(error)
        return

    if not bookings:
        st.info("No bookings found.")
        return

    filtered_bookings = render_admin_booking_filters(bookings)

    if not filtered_bookings:
        st.info("No bookings match the selected filters.")
        return

    render_admin_bookings_table(filtered_bookings)
    render_admin_booking_cards(filtered_bookings)


def get_admin_booking_filter_options(bookings: list[dict], field_name: str) -> list[str]:
    values = {
        status_to_table_text(booking.get(field_name))
        for booking in bookings
        if booking.get(field_name)
    }

    return sorted(values)


def get_admin_booking_name_options(bookings: list[dict], field_name: str) -> list[str]:
    values = {
        booking.get(field_name)
        for booking in bookings
        if booking.get(field_name)
    }

    return sorted(values)


def render_admin_booking_filters(bookings: list[dict]) -> list[dict]:
    st.subheader("Booking Filters")

    status_options = get_admin_booking_filter_options(bookings, "status")
    payment_options = get_admin_booking_filter_options(bookings, "payment_status")
    provider_options = get_admin_booking_name_options(bookings, "provider_name")
    customer_options = get_admin_booking_name_options(bookings, "customer_name")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        selected_status = st.selectbox(
            "Booking Status",
            ["All"] + status_options,
            key="admin_booking_status_filter",
        )

    with col2:
        selected_payment = st.selectbox(
            "Payment Status",
            ["All"] + payment_options,
            key="admin_booking_payment_filter",
        )

    with col3:
        selected_provider = st.selectbox(
            "Provider",
            ["All"] + provider_options,
            key="admin_booking_provider_filter",
        )

    with col4:
        selected_customer = st.selectbox(
            "Customer",
            ["All"] + customer_options,
            key="admin_booking_customer_filter",
        )

    search = st.text_input(
        "Search",
        placeholder="Booking ID, customer, provider, service, status, payment...",
        key="admin_booking_search_filter",
    )

    filtered = []

    for booking in bookings:
        booking_status = status_to_table_text(booking.get("status"))
        payment_status = status_to_table_text(booking.get("payment_status"))

        if selected_status != "All" and booking_status != selected_status:
            continue

        if selected_payment != "All" and payment_status != selected_payment:
            continue

        if selected_provider != "All" and booking.get("provider_name") != selected_provider:
            continue

        if selected_customer != "All" and booking.get("customer_name") != selected_customer:
            continue

        filtered.append(booking)

    filtered = _filter_rows(
        filtered,
        search,
        [
            "id",
            "customer_name",
            "provider_name",
            "service_title",
            "status",
            "payment_status",
        ],
    )

    st.caption(f"Showing {len(filtered)} of {len(bookings)} bookings.")

    return filtered


def render_admin_bookings_table(bookings: list[dict]):
    table_data = [
        {
            "ID": booking.get("id"),
            "Customer": booking.get("customer_name"),
            "Provider": booking.get("provider_name"),
            "Service": booking.get("service_title"),
            "Start": format_datetime(booking.get("slot_start")),
            "End": format_datetime(booking.get("slot_end")),
            "Booking Status": status_to_table_text(booking.get("status")),
            "Payment Status": status_to_table_text(booking.get("payment_status")),
            "Slot ID": booking.get("schedule_id") or "-",
        }
        for booking in bookings
    ]

    st.dataframe(
        pd.DataFrame(table_data),
        use_container_width=True,
        hide_index=True,
    )


def get_admin_booking_status_upper(booking: dict) -> str:
    return str(booking.get("status") or "").upper()


def can_admin_force_confirm_booking(booking: dict) -> bool:
    return get_admin_booking_status_upper(booking) == "PENDING"


def can_admin_force_cancel_booking(booking: dict) -> bool:
    return get_admin_booking_status_upper(booking) not in {
        "CANCELED",
        "CANCELLED",
        "REJECTED",
    }


def render_admin_booking_cards(bookings: list[dict]):
    st.subheader("Manage Bookings")

    for booking in bookings:
        booking_id = booking.get("id")

        with st.expander(
            f"Manage booking #{booking_id} — "
            f"{booking.get('customer_name')} / {booking.get('service_title')}"
        ):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.write(f"**Customer:** {booking.get('customer_name') or '-'}")
                st.write(f"**Provider:** {booking.get('provider_name') or '-'}")
                st.write(f"**Service:** {booking.get('service_title') or '-'}")

            with col2:
                st.write(f"**Start:** {format_datetime(booking.get('slot_start'))}")
                st.write(f"**End:** {format_datetime(booking.get('slot_end'))}")
                st.write(f"**Slot ID:** {booking.get('schedule_id') or '-'}")

            with col3:
                st.write(f"**Booking Status:** {status_to_table_text(booking.get('status'))}")
                st.write(f"**Payment Status:** {status_to_table_text(booking.get('payment_status'))}")

            action_col1, action_col2 = st.columns(2)

            with action_col1:
                if st.button(
                    "Force Approve / Confirm",
                    key=f"admin_confirm_booking_{booking_id}",
                    disabled=not can_admin_force_confirm_booking(booking),
                    use_container_width=True,
                ):
                    try:
                        force_confirm_admin_booking(
                            st.session_state.user_id,
                            booking_id,
                        )
                        st.success(f"Booking #{booking_id} confirmed.")
                        st.rerun()
                    except Exception as error:
                        show_action_error(error)

            with action_col2:
                confirm_cancel = st.checkbox(
                    "Confirm force cancel",
                    key=f"admin_force_cancel_confirm_{booking_id}",
                    disabled=not can_admin_force_cancel_booking(booking),
                )

                if st.button(
                    "Force Cancel",
                    key=f"admin_cancel_booking_{booking_id}",
                    disabled=(
                        not can_admin_force_cancel_booking(booking)
                        or not confirm_cancel
                    ),
                    use_container_width=True,
                ):
                    try:
                        force_cancel_admin_booking(
                            st.session_state.user_id,
                            booking_id,
                        )
                        st.success(f"Booking #{booking_id} canceled.")
                        st.rerun()
                    except Exception as error:
                        show_action_error(error)


def render_admin_reviews():
    page_title(
        "Review Management",
        "Inspect all service reviews across customers, providers, and services.",
    )

    try:
        reviews = fetch_admin_reviews(st.session_state.user_id)
    except Exception as error:
        show_action_error(error)
        return

    if not reviews:
        st.info("No reviews found.")
        return

    filtered_reviews = render_admin_review_filters(reviews)

    if not filtered_reviews:
        st.info("No reviews match the selected filters.")
        return

    render_admin_review_summary(filtered_reviews, reviews)
    render_admin_reviews_table(filtered_reviews)
    render_admin_review_cards(filtered_reviews)


def get_admin_review_name_options(reviews: list[dict], field_name: str) -> list[str]:
    values = {
        review.get(field_name)
        for review in reviews
        if review.get(field_name)
    }

    return sorted(values)


def render_admin_review_filters(reviews: list[dict]) -> list[dict]:
    st.subheader("Review Filters")

    service_options = get_admin_review_name_options(reviews, "service_title")
    provider_options = get_admin_review_name_options(reviews, "provider_name")

    col1, col2, col3 = st.columns(3)

    with col1:
        selected_rating = st.selectbox(
            "Rating",
            ["All", 5, 4, 3, 2, 1],
            key="admin_review_rating_filter",
        )

    with col2:
        selected_service = st.selectbox(
            "Service",
            ["All"] + service_options,
            key="admin_review_service_filter",
        )

    with col3:
        selected_provider = st.selectbox(
            "Provider",
            ["All"] + provider_options,
            key="admin_review_provider_filter",
        )

    search = st.text_input(
        "Search",
        placeholder="Customer, provider, service, comment...",
        key="admin_review_search_filter",
    )

    filtered = []

    for review in reviews:
        if selected_rating != "All" and review.get("rating") != selected_rating:
            continue

        if selected_service != "All" and review.get("service_title") != selected_service:
            continue

        if selected_provider != "All" and review.get("provider_name") != selected_provider:
            continue

        filtered.append(review)

    filtered = _filter_rows(
        filtered,
        search,
        [
            "id",
            "booking_id",
            "service_title",
            "provider_name",
            "customer_name",
            "comment",
        ],
    )

    st.caption(f"Showing {len(filtered)} of {len(reviews)} reviews.")

    return filtered


def render_admin_review_summary(filtered_reviews: list[dict], all_reviews: list[dict]):
    filtered_count = len(filtered_reviews)
    total_count = len(all_reviews)

    if filtered_count:
        average_rating = (
            sum(int(review.get("rating") or 0) for review in filtered_reviews)
            / filtered_count
        )
    else:
        average_rating = 0

    five_star_count = sum(
        1 for review in filtered_reviews
        if int(review.get("rating") or 0) == 5
    )

    low_rating_count = sum(
        1 for review in filtered_reviews
        if int(review.get("rating") or 0) <= 2
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Reviews Shown", filtered_count)

    with col2:
        st.metric("Total Reviews", total_count)

    with col3:
        st.metric(
            "Average Rating",
            f"{average_rating:.1f}/5" if filtered_count else "-",
        )

    with col4:
        st.metric("Low Ratings", low_rating_count)

    rating_counts = {
        rating: sum(
            1 for review in filtered_reviews
            if int(review.get("rating") or 0) == rating
        )
        for rating in [5, 4, 3, 2, 1]
    }

    st.subheader("Rating Distribution")
    st.bar_chart(pd.DataFrame({"count": rating_counts}).T)

    st.caption(f"Five-star reviews in current filter: {five_star_count}")


def render_admin_reviews_table(reviews: list[dict]):
    table_data = [
        {
            "Review ID": review.get("id"),
            "Booking ID": review.get("booking_id"),
            "Service": review.get("service_title"),
            "Provider": review.get("provider_name"),
            "Customer": review.get("customer_name"),
            "Rating": review.get("rating"),
            "Comment": review.get("comment") or "-",
            "Created": review.get("created_at_text"),
        }
        for review in reviews
    ]

    st.dataframe(
        pd.DataFrame(table_data),
        use_container_width=True,
        hide_index=True,
    )


def render_admin_review_cards(reviews: list[dict]):
    st.subheader("Review Details")

    for review in reviews:
        review_id = review.get("id")

        with st.expander(
            f"Review #{review_id} — "
            f"{review.get('rating')}/5 — "
            f"{review.get('service_title')}"
        ):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.write(f"**Customer:** {review.get('customer_name') or '-'}")
                st.write(f"**Provider:** {review.get('provider_name') or '-'}")
                st.write(f"**Service:** {review.get('service_title') or '-'}")

            with col2:
                st.write(f"**Rating:** {review.get('rating')}/5")
                st.write(f"**Booking ID:** {review.get('booking_id') or '-'}")
                st.write(f"**Created:** {review.get('created_at_text') or '-'}")

            with col3:
                st.write("**Comment:**")
                st.write(review.get("comment") or "-")

            st.caption(
                "Read-only review inspection. Edit/delete actions are not shown "
                "because the backend does not expose review moderation actions."
            )


def render_admin_reports():
    page_title("Admin Reports", "Prepare and download admin, customer, and provider PDF reports.")

    try:
        users = fetch_admin_users(st.session_state.user_id)
    except Exception as error:
        show_action_error(error)
        return

    providers = [u for u in users if u.get("role") == "PROVIDER"]
    customers = [u for u in users if u.get("role") == "CUSTOMER"]

    st.subheader("Admin statistics")

    if st.button("Prepare Admin Statistics PDF", key="prepare_admin_stats_pdf", use_container_width=True):
        try:
            st.session_state.admin_stats_pdf_bytes = admin_stats_pdf_bytes(st.session_state.user_id)
            st.success("Admin statistics PDF is ready.")
        except Exception as error:
            show_action_error(error)

    if st.session_state.get("admin_stats_pdf_bytes"):
        st.download_button(
            "Download Admin Statistics PDF",
            data=st.session_state.admin_stats_pdf_bytes,
            file_name="admin_stats.pdf",
            mime="application/pdf",
            key="download_admin_stats_pdf",
            use_container_width=True,
        )

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Provider bookings")

        if providers:
            provider_map = {f"{u.get('username')} | #{u.get('id')}": u.get("id") for u in providers}
            provider_label = st.selectbox(
                "Provider report",
                list(provider_map.keys()),
                key="provider_report_select",
            )
            provider_id = provider_map[provider_label]

            if st.button("Prepare Provider Bookings PDF", key="prepare_provider_pdf", use_container_width=True):
                try:
                    st.session_state.provider_pdf_bytes = provider_bookings_pdf_bytes(provider_id)
                    st.session_state.provider_pdf_id = provider_id
                    st.success("Provider bookings PDF is ready.")
                except Exception as error:
                    show_action_error(error)

            if (
                st.session_state.get("provider_pdf_bytes")
                and st.session_state.get("provider_pdf_id") == provider_id
            ):
                st.download_button(
                    "Download Provider Bookings PDF",
                    data=st.session_state.provider_pdf_bytes,
                    file_name=f"provider_{provider_id}_bookings.pdf",
                    mime="application/pdf",
                    key=f"download_provider_pdf_{provider_id}",
                    use_container_width=True,
                )
        else:
            st.info("No providers available for report export.")

    with col2:
        st.subheader("Customer bookings")

        if customers:
            customer_map = {f"{u.get('username')} | #{u.get('id')}": u.get("id") for u in customers}
            customer_label = st.selectbox(
                "Customer report",
                list(customer_map.keys()),
                key="customer_report_select",
            )
            customer_id = customer_map[customer_label]

            if st.button("Prepare Customer Bookings PDF", key="prepare_customer_pdf", use_container_width=True):
                try:
                    st.session_state.customer_pdf_bytes = customer_bookings_pdf_bytes(customer_id)
                    st.session_state.customer_pdf_id = customer_id
                    st.success("Customer bookings PDF is ready.")
                except Exception as error:
                    show_action_error(error)

            if (
                st.session_state.get("customer_pdf_bytes")
                and st.session_state.get("customer_pdf_id") == customer_id
            ):
                st.download_button(
                    "Download Customer Bookings PDF",
                    data=st.session_state.customer_pdf_bytes,
                    file_name=f"customer_{customer_id}_bookings.pdf",
                    mime="application/pdf",
                    key=f"download_customer_pdf_{customer_id}",
                    use_container_width=True,
                )
        else:
            st.info("No customers available for report export.")